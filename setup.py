# coding: utf-8

import os
from setuptools import setup

NAME = 'jupyter-mdk'
VERSION = '0.1.1'

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name=NAME,
    version=VERSION,
    description='Jupyter Model Development Kit',
    author_email='',
    url='https://github.com/Open-MBEE/jupyter-mdk',
    keywords=['MDK', 'Jupyter', 'MMS'],
    install_requires=read('requirements.txt').strip().split('\n'),
    packages=['mmscontents'],
    include_package_data=True,
    license='Apache 2.0',
    long_description=read('README.md'),
    long_description_content_type='text/markdown'
)
