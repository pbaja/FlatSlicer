import logging as log
import numpy as np
import numba as nb
from pathlib import Path

from .job import LaserJob, LaserUnit
from .raster import RasterImage
from utils import PerfTool, Octoprint
from utils.math import *

@nb.njit(array1d_t(array2d_t, int_t))
def intersect(points, y):
    results = []
    for i in nb.prange(len(points)-1):
        # Line points
        a = points[i]
        b = points[i+1]
        # Skip horizontal lines
        ba = b[1] - a[1]
        if ba == 0: continue

        # Calculate slope
        ya = y - a[1]
        t = ya / ba
        if t > 1.0 or t < 0.0: continue
        x = (1.0 - t) * a[0] + t * b[0]
        results.append(int(x))
    return np.array(results, dtype=np.int32)

class Gcode:
    '''
    Generates Gcode from RasterImage 
    '''
    def __init__(self, img:RasterImage):
        self._img = img
        self.job = None
        self.output = None
        self.info_calctime = None

    def _generate_outline(self, config) -> None:
        for polygon in self._img.polygons:
            # Move to start
            self.job.travel(polygon[0])
            # Burn lines
            for point in polygon[1:]:
                self.job.burn(point)
        self.job.power_off()

    def _generate_infill(self, config) -> None:
        # No polygons?
        polygons_len = len(self._img.polygons)
        if polygons_len == 0:
            log.error(f'No polygons')
            return
        print(f'num: {polygons_len}')
        
        # Calculate bbox
        bbox = calc_bbox(self._img.polygons[0])
        # for points in self._img.polygons[1:]:
        #     new_bbox = calc_bbox(points)
        #     if new_bbox[0] < bbox[0]: bbox[0] = new_bbox[0]
        #     if new_bbox[1] > bbox[1]: bbox[1] = new_bbox[1]
        #     if new_bbox[2] < bbox[2]: bbox[2] = new_bbox[2]
        #     if new_bbox[3] > bbox[3]: bbox[3] = new_bbox[3]
        print(bbox)

        # Iterate over all polygons
        # line_spacing = max(int(config.get_value('infill.line_spacing') * self._img.info_mm2pix), 1)
        # for points in self._img.polygons:
        #     bbox = calc_bbox(points) # xmin, xmax, ymin, ymax
        #     for y in range(bbox[2], bbox[3], line_spacing):
        #         # Get all intersections
        #         result = intersect(points, y)

    def generate(self, config):
        # Prepare job
        self.job = LaserJob(config)
        self.job.begin_header()
        self.job.move([0,0,0], unit=LaserUnit.Milimeters)
        self.perf = PerfTool()

        # Outline
        if config.get_value('outline.passes') > 0:
            self.job.begin_outline()
            self._generate_outline(config)
            self.perf.tick('outline')

        # Infill
        if config.get_value('infill.passes') > 0:
            self.job.begin_infill()
            self._generate_infill(config)
            self.perf.tick('infill')

        # Done
        self.job.end()
        
        self.info_calctime = self.perf.total()
        log.info(f'Gcode for {self._img.image_path.name}, ' + str(self.perf))

    def get_output(self):
        if self.job is not None:
            # Apply
            height = self._img.info_height
            pix2mm = 1 / self._img.info_mm2pix
            self.job.apply(height, pix2mm)
            log.info(f'Gcode applied, flipped y and converted pix2mm')

            # Generate output
            return str(self.job)
        return None