#! /usr/bin/env python

import os
from setuptools import setup

setup(name = 'bottleneck',
      version = '0.1.0',
      description = 'performance report generator for OpenMP programs in GNU/Linux',
      long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
      author = 'Andres More',
      author_email='more.andres@gmail.com',
      url='https://github.com/moreandres/bt',
      packages= [ 'bottleneck' ],
      entry_points = { 'console_scripts': [ 'bt = bottleneck:main' ] },
      data_files = [ ( 'config', [ 'cfg/bt.cfg', 'cfg/bt.tex' ] ) ],
      classifiers = [
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Benchmark',
        'Topic :: Utilities',
        ],
      include_package_data = True,
      test_suite='tests',
      )
