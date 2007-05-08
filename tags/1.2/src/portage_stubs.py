#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# based on gentoo portage 2.1.1, Copyright 1998-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import re, string, os, md5
from etcproposals.etcproposals_tools import get_command_output_iterator

# portage constants

VDB_PATH = "/var/db/pkg"


class NotImplementedError(Exception):
    pass

# portage utils stuff
class PortageUtils(object):
    @staticmethod
    def get_config_protect():
        for line in get_command_output_iterator(['emerge', '--info']):
            match = re.match(r'CONFIG_PROTECT="(.*)"', line)
            if match:
                return match.group(1).split(' ')
        return []


# pkgcore utils stuff
class PkgcoreUtils(object):
    @staticmethod
    def get_config_protect():
        for line in get_command_output_iterator(['pconfig', 'dump-uncollapsed']):
            match = re.match(r"'CONFIG_PROTECT' = '(.*)'", line)
            if match:
                return match.group(1).split(' ')
        return []


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
    def get_config_protect(backend):
        return {
            'portage' : PortageUtils.get_config_protect,
            'pkgcore' : PkgcoreUtils.get_config_protect
            }[backend]()

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
