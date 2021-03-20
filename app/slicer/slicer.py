import logging as log
from pathlib import Path
from utils import Event
from typing import List, Dict
from uuid import UUID

from .raster import RasterImage

class Slicer:
    '''
    Provides slicing capabilities
    '''
    
    def __init__(self) -> None:
        self.image_loaded:Event = Event()
        self._images:Dict[str, RasterImage] = {}

    def init(self) -> None:
        pass

    def load_image(self, file_path:Path) -> RasterImage:
        # Load image from disk
        image = RasterImage(file_path)
        if image.load():
            self._images[str(file_path.resolve())] = image
            self.image_loaded(image)
            log.info(f'Loaded image from {file_path}')
            return image
        else:
            return None

    def get_image(self, file_path:Path, load:bool=False) -> RasterImage:
        # Get image from array
        str_path = str(file_path.resolve())
        img = self._images.get(str_path, None)
        if img is not None: return img
        # Load if not exists
        if load: return self.load_image(file_path)
        return None