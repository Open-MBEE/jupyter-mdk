# coding: utf-8

from setuptools import setup, find_packages  # noqa: H301
from os.path import join, dirname, abspath

NAME = "mmscontents"
VERSION = "0.0.1"

def read_requirements(basename):
    reqs_file = join(dirname(abspath(__file__)), basename)
    with open(reqs_file) as f:
        return [req.strip() for req in f.readlines()]

REQUIRES = read_requirements('requirements.txt')

setup(
    name=NAME,
    version=VERSION,
    description="MMS ContentsManager for Jupyter",
    author_email="",
    url="https://github.com/Open-MBEE/mmscontents",
    keywords=["MMS", "Jupyter"],
    install_requires=REQUIRES,
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    license="Apache 2.0",
    long_description="""\
    
    """
)
