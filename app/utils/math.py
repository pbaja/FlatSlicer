import numpy as np
import numba as nb

# Types
float_t = nb.float64
int_t = nb.int32
byte_t = nb.uint8
array_t = nb.types.Array
list_t = nb.types.List

array1d_t = array_t(int_t, 1, 'C')
array2d_t = array_t(int_t, 2, 'C')
bytearray2d_t = array_t(byte_t, 2, 'C')

# Functions
@nb.njit(array1d_t(int_t, int_t))
def vec2(x:int, y:int) -> np.ndarray:
    return np.array([x, y], dtype=int_t)

@nb.njit([float_t(array1d_t, array1d_t)])
def sqdist(a:np.ndarray, b:np.ndarray) -> float:
    '''
    Returns squared distance between two points
    '''
    return (b[0]-a[0])**2 + (b[1]-a[1])**2

def calc_bbox(points):
    '''
    Returns bouding box array in form of xmin, xmax, ymin, ymax
    '''
    min_xy = np.min(points, axis=0)
    max_xy = np.max(points, axis=0)
    return np.array([min_xy[0], max_xy[0], min_xy[1], max_xy[1]])