import numba as nb

# Basic
int_t = nb.int64
float_t = nb.float64
byte_t = nb.uint8
list_t = nb.types.List

# Arrays
floatarray_t = nb.types.Array(float_t, 1, 'C')
floatarray2d_t = nb.types.Array(float_t, 2, 'C')
bytearray2d_t = nb.types.Array(byte_t, 2, 'C')

# Tuple
inttuple2_t = nb.types.UniTuple(int_t, 2)

# Lists
floatlist_t = nb.types.List(dtype=float_t)

# Functions
@nb.njit(float_t(inttuple2_t, inttuple2_t))
def sqdist(a, b):
    return (b[0]-a[0])**2 + (b[1]-a[1])**2