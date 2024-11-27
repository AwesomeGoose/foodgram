from enum import Enum


class Role(Enum):
    USER = 'user'
    ADMIN = 'admin'
    MODERATOR = 'moderator'

    @classmethod
    def choices(cls):
        return tuple((i.value, i.value) for i in cls)
