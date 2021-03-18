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

@nb.njit(_list_array1_float32(_array2_float32, nb.float64))
def _rdp(points, epsilon):
    start = 0
    end = len(points)-1
    stack = [[start, end]]
    mask = np.ones(end - start + 1, dtype=np.bool8)

    while stack:
        # Next in stack
        start, end = stack.pop()

        # Find max distance
        dist_max = 0.0
        dist_idx = start
        for idx in range(dist_idx + 1, end):
            if mask[idx]:
                dist = _pldist(points[idx], points[start], points[end])
                if dist > dist_max:
                    dist_idx = idx
                    dist_max = dist

        # Check if distance is greater than epsilon
        if dist_max > epsilon:
            stack.append([start, dist_idx])
            stack.append([dist_idx, end])
        else:
            for idx in range(start + 1, end):
                mask[idx] = False

    # Apply mask
    result = []
    for idx in range(len(points)):
        if mask[idx]:
            result.append(points[idx])
    return result

def _rdp_all(arrays, epsilon):
    result = []
    for idx in nb.prange(len(arrays)):
        result.append(_rdp(arrays[idx], epsilon))
    return result


def rdp_simplify(points, epsilon):
    # Convert list of tuples to numpy array
    array = np.array(points, dtype=np.float32)
    # Create result with rdp algorithm
    return _rdp(array, epsilon)

def rdp_simplify_all(polygons, epsilon):
    # Convert lists to arrays
    arrays = []
    for polygon in polygons:
        array = np.array(polygon, dtype=np.float32)
        arrays.append(array)
    # Simplify all
    print(nb.typeof(arrays))
    return _rdp_all(arrays, epsilon)