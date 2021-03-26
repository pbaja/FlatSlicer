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
    for i in range(len(points)-1):
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
        # Calculate x
        x = (1.0 - t) * a[0] + t * b[0]
        results.append(int(x))

        # print('---')
        # print(str(i))
        # print(str(int(x)))
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
        
        # Calculate bboxes
        polygons = self._img.polygons
        polygons_len = len(polygons)
        bboxes = np.zeros((len(polygons), 4), dtype=np.int32)
        for i in range(polygons_len):
            bboxes[i] = calc_bbox(polygons[i])

        # Generate lines
        height = self._img.image.size[1]
        line_spacing = max(int(config.get_value('infill.line_spacing') * self._img.info_mm2pix), 1)
        for y in range(0, height, line_spacing):
            # Iterate over polygons
            for i in range(polygons_len):
                # Skip outside bbox
                bbox = bboxes[i] # 0:xmin, 1:xmax, 2:ymin, 3:ymax
                if y < bbox[2] or y > bbox[3]: continue
                # Get intersections
                points = polygons[i]
                results = intersect(points, y)

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