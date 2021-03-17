import logging as log
from pathlib import Path
from utils import Event
from typing import List
from uuid import UUID

from .raster import RasterImage

class Slicer:
    '''
    Provides slicing capabilities
    '''
    
    def __init__(self) -> None:
        self.image_loaded:Event = Event()
        self._images:List[RasterImage] = []

    def init(self) -> None:
        pass

    def load_image(self, file_path:Path) -> RasterImage:
        image = RasterImage(file_path)
        if image.load():
            self._images.append(image)
            self.image_loaded(image)
            log.info(f'Loaded image from {file_path}')
            return image
        else:
            return None

    def get_image(self, unique_id:UUID=None, file_path:Path=None) -> RasterImage:
        # Get by unique id
        if unique_id is not None:
            img = next((img for img in self._images if img.unique_id == unique_id), None)
            if img is not None: return img
        # Get by file path
        if file_path is not None:
            file_path = file_path.resolve()
            img = next((img for img in self._images if img.image_path == file_path), None)
            if img is not None: return img
        # Failed
        return None