#! /usr/bin/env python

import os
from setuptools import setup

readme = os.path.join(os.path.dirname(__file__), 'README.md')

setup(name = 'bottleneck',
      version = '0.1.0',
      description = 'performance report generator for OpenMP programs in GNU/Linux',
      long_description = open(readme).read(),
      author = 'Andres More',
      author_email='more.andres@gmail.com',
      url='https://github.com/moreandres/bottleneck.git',
      packages= [ 'bottleneck' ],
      entry_points = { 'console_scripts': [ 'bt = bottleneck.bottleneck:main' ] },
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
      zip_safe = False,
      test_suite = 'tests',
#      include_package_data = True,
#      install_requires=[ 'numpy', 'scipy', 'matplotlib' ],
      )
