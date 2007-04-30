#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a tool to integrate modified configs, post-emerge

from etcproposals_lib import FrontendFailedException


class Option(object):
    def __init__(self, name, command, description):
        self.name = name
        self.command = command
        self.description = description

    def prettify(self):
        return '%s%s' % (self.command.ljust(20), self.description)


class Options(list):
    def prettify(self):
        result = 'Options:\n'
        for option in self:
            result = result + option.prettify() + '\n'
        return result


class Version(object):
    def __init__(self, shortname, name, versionnumber, authors):
        self.shortname = shortname
        self.name = name
        self.versionnumber = versionnumber
        self.authors = authors
    def prettify(self):
        return '%sversion %s by %s' % (self.name.ljust(20), self.versionnumber, self.authors)


class Versions(list):
    def prettify(self):
        result = 'Versions:\n'
        for option in self:
            result = result + option.prettify() + '\n'
        return result


OPTIONS = Options()
OPTIONS.append(Option('gtk2', '--frontend=gtk2', 'use the gtk2 frontend'))
OPTIONS.append(Option('qt4', '--frontend=qt4', 'use the qt4 frontend'))
OPTIONS.append(Option('readline', '--frontend=readline', 'use the readline frontend (requires an terminal)'))
OPTIONS.append(Option('fastexit', '--fastexit', 'automatically exit if there are no files to update'))
OPTIONS.append(Option('version', '--version', 'print version information'))

VERSIONS = Versions()

from etcproposals_lib import __version__ as libversion
from etcproposals_lib import __author__ as libauthor
VERSIONS.append(Version('lib', 'Library', libversion, libauthor))
del libversion, libauthor

try:
    from etcproposals_gtk2 import __version__ as gtk2feversion
    from etcproposals_gtk2 import __author__ as gtk2feauthor
    VERSIONS.append(Version('gtk2', 'Gtk2 Frontend', gtk2feversion, gtk2feauthor))
    del gtk2feversion, gtk2feauthor
except FrontendFailedException, e:
    pass

try:
    from etcproposals_qt4 import __version__ as qt4feversion
    from etcproposals_qt4 import __author__ as qt4feauthor
    VERSIONS.append(Version('qt4', 'Qt4 Frontend', qt4feversion, qt4feauthor))
    del qt4feversion, qt4feauthor
except FrontendFailedException, e:
    pass
    
try:
    from etcproposals_readline import __version__ as readlinefeversion
    from etcproposals_readline import __author__ as readlinefeauthor
    VERSIONS.append(Version('readline', 'Readline Frontend', readlinefeversion, readlinefeauthor))
    del readlinefeversion, readlinefeauthor
except FrontendFailedException, e:
    pass

MUST_RUN_AS_ROOT = True;

__ALL__ = [OPTIONS, VERSIONS, MUST_RUN_AS_ROOT]

if __name__ == '__main__':
    print 'etc-proposals version and options info'
    print VERSIONS.prettify()
    print OPTIONS.prettify()
