import uuid, time
import logging as log
import numpy as np
import numba as nb
from typing import List
from pathlib import Path
from enum import IntEnum
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS as ExifTags

from ..utils import Config, PerfTool, rdp_simplify_all
from .math import *

class Pixel(IntEnum):
    Black = 0
    White = 1
    Outline = 2
    Visited = 3

@nb.njit(int_t(bytearray2d_t, int_t, int_t))
def _neighbours_sum(a, x, y) -> int:
    n1 = a[x-1, y+1] == Pixel.Black
    n2 = a[x  , y+1] == Pixel.Black
    n3 = a[x+1, y+1] == Pixel.Black
    n4 = a[x+1, y  ] == Pixel.Black
    n5 = a[x+1, y-1] == Pixel.Black
    n6 = a[x  , y-1] == Pixel.Black
    n7 = a[x-1, y-1] == Pixel.Black
    n8 = a[x-1, y  ] == Pixel.Black
    return n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8

@nb.njit(bytearray2d_t(bytearray2d_t), parallel=True)
def _extract_outline(pixels) -> np.ndarray:
    w, h = pixels.shape
    for y in nb.prange(1, h-1):
        for x in nb.prange(1, w-1):
            if pixels[x, y] == Pixel.Black:
                continue
            n = _neighbours_sum(pixels, x, y)
            if n > 0:
                pixels[x, y] = Pixel.Outline
    return pixels

@nb.njit(int_t(bytearray2d_t, int_t, int_t))
def _direction(pixels, x, y):
    if pixels[y, x-1] == Pixel.Outline: return 1
    elif pixels[y, x+1] == Pixel.Outline: return 2
    elif pixels[y-1, x] == Pixel.Outline: return 3
    elif pixels[y+1, x] == Pixel.Outline: return 4
    elif pixels[y-1, x-1] == Pixel.Outline: return 5
    elif pixels[y-1, x+1] == Pixel.Outline: return 6
    elif pixels[y+1, x-1] == Pixel.Outline: return 7
    elif pixels[y+1, x+1] == Pixel.Outline: return 8
    return 0

@nb.njit(list_t(inttuple2_t)(bytearray2d_t, int_t, int_t), fastmath=True)
def _travel(pixels, x, y) -> List:
    pixels[y, x] = Pixel.Visited
    result = []
    reverse = False
    curr_dir = 0
    prev_dir = 0
    prev2_dir = 0

    deltas = [
        (99, 99), # INVALID
        (-1,  0), # Left
        ( 1,  0), # Right
        ( 0, -1), # Up
        ( 0,  1), # Down
        (-1, -1), # Left-Up
        ( 1, -1), # Right-Up
        (-1,  1), # Left-Down
        ( 1,  1), # Right-Down
    ]

    while True:
        # Get next pixel direction
        curr_dir = _direction(pixels, x, y)
        delta = deltas[curr_dir]
        if curr_dir == 0:
            # No more pixels to travel
            if reverse:
                # Check if can be closed
                start = result[0] 
                if sqdist(start, result[-1]) > 4:
                    # Backtrack for a few steps
                    retry = False
                    for i in range(5):
                        temp = result[-i-1]
                        # Maybe we are within start (2px)
                        if sqdist(start, temp) < 4:
                            result[-1] = result[0]
                            return result
                        # Maybe we can take another direction
                        if _direction(pixels, temp[0], temp[1]) != 0:
                            retry = True
                            for _ in range(i): result.pop()
                            x = temp[0]
                            y = temp[1]
                            break
                    # Found another way
                    if retry: continue
                    # Failed to close polygon, do it crude way
                    #print('warn: failed to close polygon')
                    result.append(result[0])
                    return result

                # Polygon closed
                result[-1] = result[0]
                return result
                
            # Get back to starting point and check if the line goes to the other direction
            else:
                result.append((x, y)) # Add final point
                reverse = True
                x = result[0][0]
                y = result[0][1]
                prev_dir = curr_dir
                continue

        # Append point if direction is going to change
        if curr_dir != prev_dir:
            # Continue only if we are not going to change back at next OR we are coming from straight line
            # This makes diagonal pixels one line instead of hundreds two pixel ones (e.g. typical pcb image went from 49k lines to 6.4k)
            next_dir = _direction(pixels, x+delta[0], y+delta[1])
            if next_dir != prev_dir or prev2_dir == prev_dir:
                if reverse: result.insert(0, (x, y))
                else: result.append((x, y))
        prev2_dir = prev_dir
        prev_dir = curr_dir

        # Move to next pixel
        x += delta[0]
        y += delta[1]

        # Mark as visited
        pixels[y, x] = Pixel.Visited

@nb.njit(list_t(floatarray2d_t)(bytearray2d_t)) # parallel=True causes artifacts
def _trace_outline(pixels) -> List:
    h, w = pixels.shape
    polygons = []
    for x in nb.prange(1, w-1):
        for y in nb.prange(1, h-1):
            # Search for outline
            p = pixels[y, x]
            if p == Pixel.Outline:
                points = _travel(pixels, x, y)
                if len(points) > 2: # At least 3 vertices make polygons
                    polygons.append(np.array(points, dtype=float_t))
    return polygons

class RasterImage:
    '''
    Allows loading raster images (png, jpg) from disk and extracting polygons from them
    '''

    def __init__(self, image_path:Path) -> None:
        self.unique_id:UUID = uuid.uuid4()
        self.pixels:np.ndarray = None
        self.traced:bool = False
        self.gcode = None

        self.image_path:Path = image_path.resolve()
        self.image:Image = None
        self.polygons:List = None

        self.exif_dpi:float = None
        self.info_dpi:float = None
        self.info_numlines:int = None
        self.info_numpolygons:int = None
        
    def _exif_dpi(self, img):
        exif = { ExifTags[k]: v for k, v in img.getexif().items() if k in ExifTags }
        # Get Unit
        unit = exif.get('ResolutionUnit', None) # 3->cm, 2->inch
        if unit is None: return None
        if unit == 1: return None # Prob pixels, not useful
        # Get resolution
        res = exif.get('XResolution', None)
        if res is None: res = exif.get('YResolution', None) 
        if res is None: return None
        # Convert mm to inch
        if unit == 3: res /= 0.3937008
        return round(res, 3)

    def load(self) -> bool:
        '''
        Opens image, converts it to grayscale and then to binary array 
        '''
        try:
            # Open image
            img = Image.open(self.image_path)
            self.exif_dpi = self._exif_dpi(img)
            # Find bg color
            rgb = img.convert('RGBA')
            pix = rgb.getpixel((0,0))
            bg = 'black'
            if pix[3] < 127 or sum(pix[:-1]) / 3 > 127: bg = 'white'
            # Replace transparency with color
            if img.mode == 'RGBA':
                background = Image.new('RGBA', img.size, bg)
                background.paste(img, (0, 0), img)
                img = background
            # Convert to grayscale
            img = img.convert('L')
            # Add 1pix border for simpler algorithms (iteration)
            img = ImageOps.expand(img, border=10, fill=bg)
            # Convert to array
            self.pixels = np.asarray(img).copy()
            # Make it binary
            self.pixels[self.pixels <= 127] = Pixel.Black
            self.pixels[self.pixels > 127] = Pixel.White
            # Image has been successfully loaded
            self.info_height_px = img.size[1]
            return True
        except Exception as e:
            print(e)
            return False

    def trace(self, config:Config) -> None:
        '''
        Tries to convert binary array with image data to polygons
        '''
        # Update dpi
        self.info_dpi = config.get_value('image.dpi')
        self.info_mm2pix = self.info_dpi / 25.4
        self.info_height = self.info_height_px / self.info_mm2pix

        perf = PerfTool()

        # Extract outline pixels
        perf.tick()
        self.pixels = _extract_outline(self.pixels)
        perf.tick('convert')

        # Trace outline
        self.polygons = _trace_outline(self.pixels)
        perf.tick('trace')

        # Done
        self.traced = True

        # Print stats
        self.info_numpolygons = len(self.polygons)
        self.info_numlines = sum([len(p) for p in self.polygons])
        self.info_calctime = perf.total()

        log.info(\
            f'Image {self.image_path.name},'\
            f' convert: {perf.history("convert")} ms,'\
            f' trace: {perf.history("trace")} ms,'\
            f' {self.info_numpolygons} polygons,'\
            f' {self.info_numlines} lines')

    def render(self) -> None:
        '''
        Creates PIL image from numpy array
        '''
        # Create grayscale image from bitmap
        output = self.pixels.copy()
        output[output == Pixel.Black] = 0 # Polygons
        output[output == Pixel.White] = 20 # Unprocessed pixels
        output[output == Pixel.Outline] = 20 # Unvisited pixels. Should not happen here.
        output[output == Pixel.Visited] = 50 # Pixels visited by tracing outline
        # Save to image
        self.image = Image.fromarray(output, 'L')

    def show(self) -> None:
        '''
        Simply shows image to the user, useful for debugging
        '''
        self.image.resize((self.image.width*4, self.image.height*4), Image.NEAREST).show()