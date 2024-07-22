import os

from setuptools import setup, find_packages

from Cython.Build import cythonize

from distutils.command import build_ext


# random bug fix: copied from https://bugs.python.org/issue35893#msg342821
def get_export_symbols(self, ext):
    parts = ext.name.split(".")
    if parts[-1] == "__init__":
        initfunc_name = "PyInit_" + parts[-2]
    else:
        initfunc_name = "PyInit_" + parts[-1]

build_ext.build_ext.get_export_symbols = get_export_symbols


EXCLUDE_FILES = [
    'src/SAGisXPlanung/__init__.py'
]


def get_ext_paths(root_dir, exclude_files):
    """get filepaths for compilation"""
    paths = []
    print(root_dir)
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.py':
                continue

            file_path = os.path.join(root, filename)
            if file_path in exclude_files:
                continue

            paths.append(file_path)
    return paths


setup(
    name='SAGisXPlanung',
    version='2.5.5',
    packages=find_packages(),
    ext_modules=cythonize(
        get_ext_paths('src/SAGisXPlanung/', EXCLUDE_FILES),
        compiler_directives={'language_level': 3}
    )
)