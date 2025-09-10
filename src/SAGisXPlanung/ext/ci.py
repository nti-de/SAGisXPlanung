import os
from functools import wraps


def skip_on_ci(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not os.environ.get('CI'):
            return func(*args, **kwargs)
    return wrapper
