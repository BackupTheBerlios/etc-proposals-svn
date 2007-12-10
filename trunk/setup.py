#!/usr/bin/env python
#! -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.dir_util import mkpath

mkpath('/etc/')
setup(
    name = 'etcproposals',
    url = 'http://etc-proposals.berlios.de',
    author = 'Björn Michaelsen, Jeremy Wickersheimer, Christian Glindkamp',
    author_email = 'bjoern.michaelsen@gmail.de',
    description = 'a set of tools for updating gentoo config files',
    license = 'GPL Version 2',
    version = '1.4',
    keywords = ['gentoo', 'config', 'tool'],
    packages = ['etcproposals'],
    package_dir = {'etcproposals' : 'src'},
    scripts = ['scripts/etc-proposals'],
    data_files = [
        ('/etc/' , ['data/etc-proposals.conf']),
        ('/usr/share/etcproposals/', 
		[
		'data/etcproposals-cvs.svg',
		'data/etcproposals-whitespace.svg',
		'data/etcproposals-unmodified.svg',
		'data/qt4_about.svgz',
		'data/qt4_add.svgz',
		'data/qt4_exit.svgz',
		'data/qt4_help.png',
		'data/qt4_ok.png',
		'data/qt4_reload.svgz'
		])]
)
