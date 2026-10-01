import ctypes


class FixedNumericArray(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint32),
        ("values", ctypes.c_double * 36),
    ]
