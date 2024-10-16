import os

# exclude when running migrations due to some circular imports
# TODO: why is this only problematic on revision updates?
if not os.environ.get('CI'):
    from . import listeners
