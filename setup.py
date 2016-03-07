#!/usr/bin/env python

from setuptools import setup
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Noodles',
    version='0.1.9240',
    description='Workflow Engine',
    author='Johan Hidding',
    url='https://github.com/NLeSC/noodles',
    packages=[
        'noodles', 'noodles.serial', 'noodles.run', 'noodles.display',
        'noodles.interface', 'noodles.workflow'],

    classifiers=[
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Distributed Computing'],

#    install_requires=['pyxenon'],

    extras_require={
        'test': ['nose', 'coverage', 'pyflakes', 'pep8']
    },
)
