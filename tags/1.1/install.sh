#!/bin/bash
python setup.py sdist
cp dist/*.tar.gz /usr/portage/distfiles
cp dist/*.ebuild /usr/local/portage/app-portage/etcproposals
