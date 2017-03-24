#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals
import sys
print( 777777, sys.path)
sys.path.pop(0)     #dont import my struct plz
sys.modules.pop('struct',None)

from setuptools import setup

name = 'svd_util'
setup(
    name= name,
    version='123',
    description='python utility funcs, classes, small languages+frameworks, scripts.',
    url='https://github.com/svilendobrev/svd_util',
    author='svilen dobrev',
    license='MIT',
    packages= [ name ] + [ name+'.'+x for x in ''' divan ext javagen py testeng ui yamls '''.split() ],
    package_dir= { 'svd_util': ''  },   #hack a little..
)

# vim:ts=4:sw=4:expandtab
