from enum import StrEnum, auto


class Stage(StrEnum):
    PROD = auto()
    DEV = auto()


class Category(StrEnum):
    BOOKS = auto()
    MOVIES = auto()
    SERIES = auto()


class ItemStatus(StrEnum):
    BACKLOG = auto()
    LOGGED = auto()
