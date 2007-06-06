#!/bin/bash
PORTDIR_OVERLAY=/usr/local/portage
DISTDIR=/usr/portage/distfiles
python setup.py sdist
mkdir -p $PORTDIR_OVERLAY/app-portage/etcproposals
cp dist/*.ebuild $PORTDIR_OVERLAY/app-portage/etcproposals
cp dist/*.tar.gz $DISTDIR
cd $PORTDIR_OVERLAY/app-portage/etcproposals
ebuild digest *.ebuild
emerge etcproposals
