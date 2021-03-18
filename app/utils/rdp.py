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

def _rdp(points, start_index, last_index, epsilon):
    stk = []
    stk.append([start_index, last_index])
    global_start_index = start_index
    indices = np.ones(last_index - start_index + 1, dtype=bool)

    while stk:
        start_index, last_index = stk.pop()

        dmax = 0.0
        index = start_index

        for i in range(index + 1, last_index):
            if indices[i - global_start_index]:
                d = _pldist(points[i], points[start_index], points[last_index])
                if d > dmax:
                    index = i
                    dmax = d

        if dmax > epsilon:
            stk.append([start_index, index])
            stk.append([index, last_index])
        else:
            for i in range(start_index + 1, last_index):
                indices[i - global_start_index] = False

    return indices


def rdp_simplify(points):
    # Convert list of tuples to numpy array
    array = np.array(points, dtype=np.float32)
    # Create mask with rdp algorithm
    mask = _rdp(array, 0, len(array)-1, 0.8)
    # Apply mask
    result = list([point for point, b in zip(array, mask) if b])
    return result