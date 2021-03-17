import uuid, time
import logging as log
import numpy as np
import numba as nb
from pathlib import Path
from enum import IntEnum
from PIL import Image



class Pixel(IntEnum):
    Black = 0
    White = 1
    Outline = 2


_array_type = nb.types.Array(nb.uint8, 2, 'C')

@nb.njit(nb.int32(_array_type, nb.int32, nb.int32))
def _neighbours(a, x, y) -> int:
    n1 = a[x-1, y+1] == Pixel.White
    n2 = a[x  , y+1] == Pixel.White
    n3 = a[x+1, y+1] == Pixel.White
    n4 = a[x+1, y  ] == Pixel.White
    n5 = a[x+1, y-1] == Pixel.White
    n6 = a[x  , y-1] == Pixel.White
    n7 = a[x-1, y-1] == Pixel.White
    n8 = a[x-1, y  ] == Pixel.White
    return n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8

@nb.njit(_array_type(_array_type), parallel=True)
def _process(arr) -> np.ndarray:
    w, h = arr.shape
    for y in nb.prange(1, h-1):
        for x in nb.prange(1, w-1):
            n = _neighbours(arr, x, y)
            if n > 0 and n < 4:
                arr[x, y] = Pixel.Outline
    return arr


class RasterImage:
    '''
    Allows loading raster images (png, jpg) from disk and vectorizing them 
    '''

    def __init__(self, image_path:Path) -> None:
        self.unique_id = uuid.uuid4()
        self.image_path:Path = image_path.resolve()
        self.pixels:np.ndarray = None
        self.output:np.ndarray = None
        
    def load(self) -> bool:
        '''
        Opens image, converts it to grayscale and then to binary array 
        '''
        try:
            # Open image
            img = Image.open(self.image_path)
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
        start_time = time.time()
        self.output = _process(self.pixels)
        elapsed = time.time()-start_time
        log.info(f'Image {self.image_path.name} converted in {round(elapsed*1000,2)} ms')

    def show(self) -> None:
        '''
        Simply shows image to the user, useful for debugging
        '''
        self.output[self.output == Pixel.Black] = 0
        self.output[self.output == Pixel.White] = 50
        self.output[self.output == Pixel.Outline] = 255

        img = Image.fromarray(self.output, 'L')
        img = img.resize((img.width*4, img.height*4), Image.NEAREST)
        img.show()

    
