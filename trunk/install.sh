#!/bin/bash
python setup.py sdist
cp dist/*.tar.gz /usr/portage/distfiles
cp dist/*1.2.ebuild /usr/local/portage/app-portage/etcproposals
cd /usr/local/portage/app-portage/etcproposals
ebuild *.ebuild digest
