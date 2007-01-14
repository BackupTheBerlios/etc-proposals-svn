#!/usr/bin/env python
#! -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.dir_util import mkpath

mkpath('/etc/')
setup(
    name = 'etcproposals',
    url = 'http://michaelsen.kicks-ass.net/Members/bjoern/etcproposals',
    author = 'Björn Michaelsen',
    author_email = 'bmichaelsen@gmx.de',
    description = 'a set of tools for updating gentoo config files',
    license = 'GPL Version 2',
    version = '0.91.20070103',
    keywords = ['gentoo', 'config', 'tool'],
    packages = ['etcproposals'],
    package_dir = {'etcproposals' : 'src'},
    scripts = ['scripts/etc-proposals'],
    data_files = [('/etc/' , ['data/etc-proposals.conf'])]
)
