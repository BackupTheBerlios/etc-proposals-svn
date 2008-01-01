#!/bin/bash
PORTDIR_OVERLAY=/usr/local/portage
DISTDIR=/usr/portage/distfiles
python setup.py sdist
mkdir -p $PORTDIR_OVERLAY/app-portage/etc-proposals
cp dist/*.ebuild $PORTDIR_OVERLAY/app-portage/etc-proposals
cp dist/*.tar.gz $DISTDIR
cd $PORTDIR_OVERLAY/app-portage/etc-proposals
ebuild *.ebuild digest
emerge etc-proposals
