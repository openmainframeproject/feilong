#!/usr/bin/env python
import setuptools

# In python < 2.7.4, a lazy loading of 
# setuptools if some other modules regi
# solution from: http://bugs.python.org
try:
    import multiprocessing  # noqa
except ImportError:
    pass

setuptools.setup(
    setup_requires=['pbr>=2.0.0'],
    pbr=True)
