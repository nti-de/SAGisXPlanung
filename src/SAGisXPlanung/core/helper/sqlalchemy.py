from sqlalchemy.orm import class_mapper, object_mapper
from sqlalchemy.orm.exc import UnmappedClassError, UnmappedInstanceError


def is_mapped(obj):
    try:
        class_mapper(obj)
    except UnmappedClassError:
        return False
    return True


def is_mapped_instance(obj):
    try:
        object_mapper(obj)
    except UnmappedInstanceError:
        return False
    return True