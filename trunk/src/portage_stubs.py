#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# based on gentoo portage 2.1.1, Copyright 1998-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import shlex, string, os, md5
portage_available = False
try:
    import portage
    portage_available = True
except ImportError:
    pass

# portage constants

VDB_PATH                = "/var/db/pkg"

PROFILE_PATH            = "/etc/make.profile"

MAKE_CONF_FILE          = "/etc/make.conf"
MAKE_GLOBALS_FILE       = "/etc/make.globals"
MAKE_DEFAULTS_FILE      = PROFILE_PATH + "/make.defaults"

class NotImplementedError(Exception):
    pass

# portage utils stuff
class PortageUtils(object):
    @staticmethod
    def getconfig(mycfg):
        def parser_state_generator():
            while True:
                for state in ['key', 'equals', 'value']:
                    yield state
        mykeys = {}
        f = open(mycfg,'r')
        lex = shlex.shlex(f)
        lex.wordchars = string.digits+string.letters+"~!@#$%*_\:;?,./-+{}"     
        lex.quotes = "\"'"
        parser_states = parser_state_generator()
        while True:
            token=lex.get_token()
            parser_state = parser_states.next()
            if token=='' or (parser_state == 'equals' and not token =='='):
                break
            if parser_state == 'key':
                key = token
            if parser_state == 'value':
                mykeys[key]=token.replace("\\\n","")
        return mykeys

    @staticmethod
    def get_config_protect():
        make_conf_settings = PortageUtils.getconfig(MAKE_CONF_FILE)
        make_globals_settings = PortageUtils.getconfig(MAKE_GLOBALS_FILE)
        make_defaults_settings = PortageUtils.getconfig(MAKE_DEFAULTS_FILE)
        config_protect = os.environ['CONFIG_PROTECT']
        for config_settings in [make_defaults_settings, make_globals_settings, make_conf_settings]:
            if config_settings.has_key('CONFIG_PROTECT'):
                config_protect = config_protect + ' ' + config_settings['CONFIG_PROTECT'][1:-1]
        return config_protect.split()


# Installed package DB stuff
class PortagePkgPart(object):
    @staticmethod
    def parse_dbcontentsline(dbcontentsline):
        if dbcontentsline.startswith('obj'):
            return PortagePkgPartObject(dbcontentsline)
        else:
            raise NotImplementedError


class PortagePkgPartObject(PortagePkgPart):
    def __init__(self, dbcontentsline):
        templine = dbcontentsline.split(' ', 1)
        self.type = templine[0]
        (self.path, self.md5, mtimestring) = templine[1].rsplit(' ', 2)     
        self.mtime = int(mtimestring)
    

class InstalledPkg(object):
    def __init__(self, dbpath):
        self.dbpath = dbpath

    def contents(self):
        result = list()
        fd = open(os.path.join(self.dbpath, 'CONTENTS'))
        for line in fd:
            line = line.replace('\n', '') 
            try:
                result.append(PortagePkgPart.parse_dbcontentsline(line))
            except NotImplementedError:
                pass
        fd.close()
        return result

    
class InstalledPkgDB(object):
    def __init__(self, dbpath = VDB_PATH):
        self.dbpath = dbpath

    def installed_pkgs_dbpaths(self):
        return  (path
            for (path, dirs, files) in os.walk(self.dbpath) for file in files
            if file == 'PF')


class PortageInterface(object):
    @staticmethod
    def get_config_protect():
        if portage_available:
            return portage.settings['CONFIG_PROTECT'].split(' ')
        return PortageUtils.get_config_protect()

    @staticmethod
    def get_md5_from_vdb(files):
        "returns a dict containing the md5s that were recorded in the vdb for the given files"
        def allpkgcontents_generator():
            for pkgdbpath in InstalledPkgDB().installed_pkgs_dbpaths():
                for pkgpart in InstalledPkg(pkgdbpath).contents():
                    yield pkgpart
        files_to_check = set(files)
        pkgparts = dict()
        allpkgcontents = allpkgcontents_generator()
        while len(files_to_check) > 0:
            try:
                pkgpart = allpkgcontents.next()
            except StopIteration:
                break
            if not pkgpart.path in files_to_check:
                continue
            pkgparts[pkgpart.path] = pkgpart.md5
            files_to_check.discard(pkgpart.path)
        return pkgparts


__all__ = ['PortageInterface']
