from enum import Enum


class ParsingState(Enum):
    STOCK = 0
    PROCESS = 1
    OPTIMIZE = 2
