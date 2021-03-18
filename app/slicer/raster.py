import uuid, time
import logging as log
import numpy as np
import numba as nb
from typing import List
from pathlib import Path
from enum import IntEnum
from PIL import Image

from utils import PerfTool, rdp_simplify

class Pixel(IntEnum):
    Black = 0
    White = 1
    Outline = 2
    Visited = 3


_pixels_array = nb.types.Array(nb.uint8, 2, 'C')
_tuple64_array = nb.types.List(nb.types.UniTuple(nb.int64, 2))
_tuple64_array2 = nb.types.List(_tuple64_array)

@nb.njit(nb.int32(_pixels_array, nb.int32, nb.int32))
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

@nb.njit(_pixels_array(_pixels_array), parallel=True)
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

@nb.njit(_tuple64_array(_pixels_array, nb.int32, nb.int32), fastmath=True)
def _travel(pixels, x, y) -> List:
    points = [(x, y)]
    point_num = 0
    point_dir = (0,0)
    last_dir = (0, 0)
    prev_point = points[0]
    while True:
        # Mark current
        pixels[y, x] = Pixel.Visited

        # Append point if direction changed
        point_num += 1
        if point_dir != last_dir:
            points.append(prev_point)
            point_dir = last_dir
            point_num = 0
        prev_point = (x, y)

        # Move left
        if pixels[y, x-1] == Pixel.Outline:
            x -= 1
            last_dir = (0, -1)
            continue
        # Move right
        if pixels[y, x+1] == Pixel.Outline:
            x += 1
            last_dir = (0, 1)
            continue
        # Move up
        if pixels[y-1, x] == Pixel.Outline:
            y -= 1
            last_dir = (-1, 0)
            continue
        # Move down
        if pixels[y+1, x] == Pixel.Outline:
            y += 1
            last_dir = (1, 0)
            continue
        
        # No outline in any direction
        points.append(prev_point)
        return points

@nb.njit(_tuple64_array2(_pixels_array)) # parallel=True causes artifacts
def _trace_outline(pixels) -> List:
    h, w = pixels.shape
    polygons = []
    for x in nb.prange(1, w-1):
        for y in nb.prange(1, h-1):
            # Search for outline
            p = pixels[y, x]
            if p == Pixel.Outline:
                points = _travel(pixels, x, y)
                if len(points) > 2:
                    polygons.append(points)
    return polygons

class RasterImage:
    '''
    Allows loading raster images (png, jpg) from disk and vectorizing them 
    '''

    def __init__(self, image_path:Path) -> None:
        self.unique_id = uuid.uuid4()
        self.image_path:Path = image_path.resolve()
        self.pixels:np.ndarray = None
        self.image:Image = None
        self.polygons:List = None
        
    def load(self) -> bool:
        '''
        Opens image, converts it to grayscale and then to binary array 
        '''
        try:
            # Open image
            img = Image.open(self.image_path)
            # Replace transparency with color
            if img.mode == 'RGBA':
                background = Image.new('RGBA', img.size, 'white')
                background.paste(img, (0, 0), img)
                img = background
            # Convert to grayscale
            img = img.convert('L')
            # Convert to array
            self.pixels = np.asarray(img).copy()
            # Make it binary
            self.pixels[self.pixels <= 127] = Pixel.Black
            self.pixels[self.pixels > 127] = Pixel.White
            # Image has been successfully loaded
            return True
        except Exception as e:
            print(e)
            return False

    def trace(self) -> None:
        '''
        Tries to convert binary array with image data to polygons
        '''
        perf = PerfTool()

        # Extract outline pixels
        perf.tick()
        self.pixels = _extract_outline(self.pixels)
        perf.tick()

        # Trace outline
        self.polygons = _trace_outline(self.pixels)
        perf.tick()

        # Simplify
        total_lines_before = sum([len(p) for p in self.polygons])
        self.polygons = [rdp_simplify(p) for p in self.polygons]
        perf.tick()

        # Print stats
        total_lines = sum([len(p) for p in self.polygons])
        log.info(\
            f'Image {self.image_path.name},'\
            f' convert: {perf.history(-3)} ms,'\
            f' trace: {perf.history(-2)} ms,'\
            f' simplify: {perf.history(-1)} ms,'\
            f' {len(self.polygons)} polygons,'\
            f' {total_lines} (+{total_lines_before-total_lines}) lines')

    def render(self) -> None:
        '''
        Creates image from numpy array
        '''
        # Create grayscale image from bitmap
        output = self.pixels.copy()
        output[output == Pixel.Black] = 0
        output[output == Pixel.White] = 50
        output[output == Pixel.Outline] = 150
        output[output == Pixel.Visited] = 255
        # Save to image
        self.image = Image.fromarray(output, 'L')

    def show(self) -> None:
        '''
        Simply shows image to the user, useful for debugging
        '''
        self.image.resize((self.image.width*4, self.image.height*4), Image.NEAREST).show()

    
