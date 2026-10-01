import ctypes


class BigSensor(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("sequence", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("row_stride", ctypes.c_uint32),
        ("encoding", ctypes.c_char_p),
        ("data_size", ctypes.c_size_t),
        ("data", ctypes.POINTER(ctypes.c_uint8)),
    ]
