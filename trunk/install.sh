#!/bin/bash
python setup.py sdist
mkdir -p /usr/local/portage/app-portage/etcproposals
cp dist/*.tar.gz /usr/portage/distfiles
cp dist/*.ebuild /usr/local/portage/app-portage/etcproposals
cd /usr/local/portage/app-portage/etcproposals
ebuild *.ebuild digest
emerge etcproposals
