# Copyright 2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit distutils

DESCRIPTION="a set of tools for updating gentoo config files"
HOMEPAGE="http://michaelsen.kicks-ass.net/users/bjoern/etcproposals"
SRC_URI="http://michaelsen.kicks-ass.net/Members/bjoern/etcproposals/downloads/${P}.tar.gz"

IUSE="gtk"
LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"

DEPEND=">=dev-lang/python-2.4.3
	gtk? (>=dev-python/pygtk-2.10)"

pkg_preinst(){
	mkdir ${D}/usr/sbin
	mv ${D}/usr/bin/etc-proposals ${D}/usr/sbin/
}
