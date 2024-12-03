# -*- coding: utf-8 -*-
from setuptools import setup


with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="tinybird-python",
    author="tinybird.co",
    author_email="support@tinybird.co",
    description="SDK around Tinybird APIs",
    version="0.1.2",
    url="https://github.com/tinybirdco/tinybird-python-sdk",
    install_requires=required,
    packages=["tb"],
)
