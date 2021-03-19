import math
from typing import List
import numba as nb
import numpy as np
from numba.np.extensions import cross2d

from . import PerfTool

_array0_float32 = nb.types.Array(nb.float32, 0, 'C')
_array1_float32 = nb.types.Array(nb.float32, 1, 'C')

@nb.njit([nb.float32(_array0_float32), nb.float32(_array1_float32)])
def _len(x:np.ndarray):
    if x.ndim == 0: return x.item()
    return np.sqrt(x[0]**2 + x[1]**2)

@nb.njit(nb.float64(_array1_float32, _array1_float32, _array1_float32))
def _pldist(point:np.ndarray, start:np.ndarray, end:np.ndarray):
    """
    Calculates the distance from point to the line defined by start, end
    """

    # If start=end, return distance to them
    if np.all(np.equal(start, end)):
        return _len(point - start)

    # Calculate cross
    cross = cross2d(end - start, start - point)
    cross_dist = np.abs(_len(cross))
    line_dist = _len(end - start)
    return np.divide(cross_dist, line_dist)


_array2_float32 = nb.types.Array(nb.float32, 2, 'C')
_array1_bool = nb.types.Array(nb.boolean, 1, 'C')
_list_array1_float32 = nb.types.List(_array1_float32)

@nb.njit(_list_array1_float32(_array2_float32, nb.float64, nb.int64, nb.int64))
def _rdp(points, epsilon, start, end):
    _start, _end = start, end
    stack = [[_start, _end]]
    mask = np.ones(_end - _start + 1, dtype=np.bool8)

    while stack:
        # Next in stack
        _start, _end = stack.pop()

        # Find max distance
        dist_max = 0.0
        dist_idx = _start
        for idx in range(dist_idx + 1, _end):
            if mask[idx - start]:
                dist = _pldist(points[idx], points[_start], points[_end])
                if dist > dist_max:
                    dist_idx = idx
                    dist_max = dist

        # Check if distance is greater than epsilon
        if dist_max > epsilon:
            stack.append([_start, dist_idx])
            stack.append([dist_idx, _end])
        else:
            for idx in range(_start + 1, _end):
                mask[idx - start] = False

    # Apply mask
    result = []
    for idx in range(start, end):
        if mask[start-idx]:
            result.append(points[idx])
    return result

_array2_int64 = nb.types.Array(nb.int64, 2, 'C')
_list_list_array1_float32 = nb.types.List(_list_array1_float32)

@nb.njit(_list_list_array1_float32(_array2_float32, _array2_int64, nb.float32))
def _rdp_all(points, indexes, epsilon):
    result = []
    for i in range(len(indexes)):
        result.append(_rdp(points, epsilon, indexes[i][0], indexes[i][1]))
    return result

def rdp_simplify(points, epsilon):
    # Convert list of tuples to numpy array
    array = np.array(points, dtype=np.float32)
    # Create result with rdp algorithm
    return _rdp(array, epsilon)

def rdp_simplify_all(polygons, epsilon):

    num_points = sum([len(p) for p in polygons])
    num_polygons = len(polygons)

    points = np.zeros([num_points, 2], dtype=np.float32)
    indexes = np.zeros([num_polygons, 2], dtype=np.int64)
    curr_index = 0
    curr_point = 0

    for polygon in polygons:
        # Append start-end index
        indexes[curr_index][0] = curr_point # Start (inclusive)
        indexes[curr_index][1] = curr_point + len(polygon) # End (exclusive)
        curr_index += 1
        # Append points
        for point in polygon:
            points[curr_point] = point
            curr_point += 1

    return _rdp_all(points, indexes, epsilon)