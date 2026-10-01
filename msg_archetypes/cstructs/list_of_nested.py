import ctypes

from .small_flat import SmallFlat


class ListOfNested(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint32),
        ("samples_count", ctypes.c_size_t),
        ("samples", ctypes.POINTER(SmallFlat)),
    ]
