"""Setup script for the PTP Optimization framework."""
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
