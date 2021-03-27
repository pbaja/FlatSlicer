import numba as nb

# Basic
int_t = nb.int64
float_t = nb.float64
byte_t = nb.uint8
list_t = nb.types.List

# Arrays
array2d_t = nb.types.Array(float_t, 2, 'C')
bytearray2d_t = nb.types.Array(byte_t, 2, 'C')

# Tuple
inttuple2_t = nb.types.UniTuple(int_t, 2)
