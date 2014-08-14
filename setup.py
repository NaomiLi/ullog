#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################################################
# 
# Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
# 
########################################################################
 
from setuptools import setup, find_packages

setup(
    name = "ullog",
    version = "1.0.0",
    packages = find_packages(),
    scripts = ["ullog/lib.py", "ullog/__init__.py"],

    description = "A logging tool",
    long_description = "Split logging at certain interval time, and configure \
        different LEVEL to different log file",
    author = "Rui Li", 
    author_email = "lirui05@baidu.com",

    keywords = ("logging", "rotated logging", "level logging"),
)
