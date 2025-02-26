from enum import Enum

class ObjType(Enum):
    SIMPLE = 0
    FUNC = 1
    CLS = 2
    CELL_REF = 5
    CELL_DIRECT = 6
    REF = 10
    MOD_IMPORT = 11

