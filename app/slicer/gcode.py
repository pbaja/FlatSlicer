import logging as log
from pathlib import Path

from .job import LaserJob
from .raster import RasterImage
from utils import PerfTool

class Gcode:
    '''
    Generates Gcode from RasterImage 
    '''
    def __init__(self, img:RasterImage):
        self._img = img
        self.job = None

    def generate(self, config):
        # Prepare job
        self.job = LaserJob(config)
        self.job.begin_header()
        self.job.move([0,0,0])

        # Outline
        perf = PerfTool()
        self.job.begin_outline()
        for polygon in self._img.polygons:
            # Move to start
            self.job.move(polygon[0])
            # Burn lines
            for end in polygon[1::2]:
                self.job.burn(end)
        self.job.power_off()
        perf.tick()

        # Done
        self.job.end()
        log.info(f'Gcode for {self._img.image_path.name}, outline: {perf.history(-1)} ms')

    def save(self, path:Path):
        if self.job is not None:
            with path.open('w+') as f:
                f.write(str(self.job))
                log.info(f'Saved Gcode to {path}')
            return True