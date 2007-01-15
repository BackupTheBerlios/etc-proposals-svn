# Copyright 2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit distutils

DESCRIPTION="a set of tools for updating gentoo config files"
HOMEPAGE="http://michaelsen.kicks-ass.net/users/bjoern/etcproposals"
SRC_URI="http://michaelsen.kicks-ass.net/Members/bjoern/etcproposals/downloads/${P}.tar.gz"

IUSE=""
LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"

DEPEND=">=sys-apps/portage-2.1"

pkg_preinst(){
	mkdir ${D}/usr/sbin
	mv ${D}/usr/bin/etc-proposals ${D}/usr/sbin/
}
