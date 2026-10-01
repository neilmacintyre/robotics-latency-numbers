import ctypes

from .small_flat import SmallFlat


class NestedListLevel2(ctypes.Structure):
    _fields_ = [
        ("items_count", ctypes.c_size_t),
        ("items", ctypes.POINTER(SmallFlat)),
    ]


class NestedListLevel1(ctypes.Structure):
    _fields_ = [
        ("items_count", ctypes.c_size_t),
        ("items", ctypes.POINTER(NestedListLevel2)),
    ]


class ListOfTriplyNested(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint32),
        ("items_count", ctypes.c_size_t),
        ("items", ctypes.POINTER(NestedListLevel1)),
    ]
