"""Setup script for the PTP Optimization framework."""
# Copyright (c) 2021 Intel
# Copyright (C) 2023 Maciek Machnikowski <maciek(at)machnikowski.net>
# Licensed under the GNU General Public License v2.0 or later (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://spdx.org/licenses/GPL-2.0-or-later.html

from setuptools import setup

with open("README.md", 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
   name='ptp-optimization',
   version='1.0',
   description='Precision Time Protocol Optimization',
   license="GPL-2.0-or-later",
   long_description=long_description,
   author='Maciek Machnikowski',
   author_email='maciek@machnikowski.net',
   packages=['ptp-optimization'],
   install_requires=['numpy', 'scikit-learn', 'matplotlib'],
   scripts=[
            'evaluate.py',
            'main.py',
            'parse_ptp.py',
           ]
)
