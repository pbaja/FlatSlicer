import logging as log
import numpy as np
import numba as nb
from pathlib import Path

from .job import LaserJob, LaserUnit
from .raster import RasterImage
from utils import PerfTool, Octoprint
from utils.math import *

array1_int = nb.types.Array(int_t, 1, 'C')
array2_int = nb.types.Array(int_t, 2, 'C')
array1_float64 = nb.types.Array(nb.float64, 1, 'C')
array2_float64 = nb.types.Array(nb.float64, 2, 'C')

@nb.njit(nb.float64(array1_int, array1_int, nb.float64))
def get_x(a, b, y):
    # Check if ba is not zero
    ba = b[1] - a[1]
    if ba == 0: return -1.0
    ya = y - a[1]

    # Find t
    t = ya / ba
    if t > 1.0 or t < 0.0: return -1.0
    return (1.0 - t) * a[0] + t * b[0]

list_float64 = nb.types.List(dtype=nb.float64)

@nb.njit(list_float64(array2_int, nb.float64))
def intersect(points, y):
    intersections = [] # X coords
    for idx in nb.prange(len(points)-1):
        p1 = points[idx]
        p2 = points[idx+1]
        x = get_x(p1, p2, y)
        if x != -1: intersections.append(x)
    return intersections

@nb.njit(int_t(array2_float64, array1_float64, nb.float64, nb.float64))
def closest(lines, prev, float_max, max_dist):
    lines_len = len(lines)
    closest_dist = float_max
    closest_idx = 0
    for idx in range(0, lines_len, 2):
        # Skip consumed
        if lines[idx] is None:
            continue
        # Get distance
        dist = sqdist(prev, lines[idx])
        if dist < closest_dist:
            closest_idx = idx
            closest_dist = dist
            if dist < max_dist: break # Good enough
    return closest_idx

class Gcode:
    '''
    Generates Gcode from RasterImage 
    '''
    def __init__(self, img:RasterImage):
        self._img = img
        self.job = None
        self.output = None
        self.info_calctime = None

    def _generate_outline(self, config):
        for polygon in self._img.polygons:
            # Move to start
            self.job.travel(polygon[0])
            # Burn lines
            for point in polygon[1:]:
                self.job.burn(point)
        self.job.power_off()
        self.perf.tick('outline')

    def _generate_infill(self, config):
        # No polygons?
        if len(self._img.polygons) == 0:
            log.error(f'No polygons')
            return

        # Calculate bounding boxes
        polygons = self._img.polygons
        float_max = np.finfo(np.float64).max
        template = np.array([float_max, -float_max, float_max, -float_max]) # min_x, max_x, min_y, max_y

        global_bbox = template.copy()
        polygon_bbox = np.zeros((len(polygons), 4), dtype=np.float64)
        for i, polygon in enumerate(polygons):
            # Calculate polygon bounding box
            bbox = template.copy()
            for p in polygon:
                if p[0] < bbox[0]: bbox[0] = p[0]
                if p[0] > bbox[1]: bbox[1] = p[0]
                if p[1] < bbox[2]: bbox[2] = p[1]
                if p[1] > bbox[3]: bbox[3] = p[1]
            polygon_bbox[i] = bbox
            # Update global bounding box
            if bbox[0] < global_bbox[0]: global_bbox[0] = bbox[0]
            if bbox[1] > global_bbox[1]: global_bbox[1] = bbox[1]
            if bbox[2] < global_bbox[2]: global_bbox[2] = bbox[2]
            if bbox[3] > global_bbox[3]: global_bbox[3] = bbox[3]
        self.perf.tick('bbox')

        # Find infill intersecting points
        infill_lines = []
        drawing_height = global_bbox[3] - global_bbox[2]
        infill_spacing = config.get_value('infill.line_spacing')
        infill_spacing *= self._img.info_mm2pix # Convert mm to pixels
        sn = int(drawing_height / infill_spacing)
        for s in range(sn):
            # Current y coord
            y = global_bbox[2] + (s/float(sn)) * drawing_height
            
            # Intersect with polygons
            points = []
            for i, polygon in enumerate(polygons):
                # Check if point is in bounding box
                if y < polygon_bbox[i][2] or y > polygon_bbox[i][3]: continue
                # Get all x intersection points
                x = intersect(polygon, y + 0.01)
                points += x
            if len(points) == 0: continue

            # Add lines
            points = sorted(points, reverse=s%2==0)
            for i in range(0, len(points)-1, 2):
                p1 = np.array([points[i], y])
                p2 = np.array([points[i+1], y])
                infill_lines += [p1, p2]

            self.job.power_off()
        self.perf.tick('infill')

        # Burn lines
        min_travel = pow(self._img.info_mm2pix * config.get_value('machine.min_travel'), 2)
        prev_a = np.zeros(1, dtype=np.float64)
        prev_b = np.zeros(1, dtype=np.float64)
        infill_lines = np.array(infill_lines)
        lines_left = len(infill_lines) // 2
        while lines_left > 0:

            # Find closest
            closest_idx = closest(infill_lines, prev_b, float_max, self._img.info_mm2pix * 0.1)
            
            # Get points
            a = infill_lines[closest_idx]
            b = infill_lines[closest_idx+1]

            # Burn
            dist = sqdist(prev_b, a)
            if dist > min_travel: self.job.travel(a) 
            else: self.job.burn(a)
            
            self.job.burn(b)
            prev_b = b

            # Remove
            infill_lines[closest_idx] = None
            #del infill_lines[closest_idx]
            lines_left -= 1
            
        self.perf.tick('burn')

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

        # Infill
        if config.get_value('infill.passes') > 0:
            self.job.begin_infill()
            self._generate_infill(config)

        # Done
        self.job.end()
        
        self.info_calctime = self.perf.total()
        log.info(f'Gcode for {self._img.image_path.name}, ' + ', '.join(f'{param}: {self.perf.history(param)} ms' for param in ['outline', 'bbox', 'infill', 'burn']))

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