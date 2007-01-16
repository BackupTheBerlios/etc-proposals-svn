#! /usr/bin/python

import os, os.path, datetime, md5, pprint

VDB_PATH = "/var/db/pkg/"

class NotImplementedError(Exception):
    pass


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
    
    def is_unchanged_in_fs(self):
        return self._is_md5_unchanged_in_fs() and self._is_mtime_unchanged_in_fs()

    def is_md5_unchanged_in_fs(self):
        try:
            fd = open(self.path)
            content = fd.read()
            fd.close()
            if md5.md5(content).hexdigest() == self.md5:
                return True
            return False
        except IOError:
            return False
        
    def is_mtime_unchanged_in_fs(self):
        try:
            if os.stat(self.path).st_mtime == self.mtime:
                return True
            return False
        except OSError:
            return False
        
def get_pkgparts(files):
    def contentfiles():
        return  (os.path.join(path, file)
            for (path, dirs, files) in os.walk(VDB_PATH) for file in files
            if file == 'CONTENTS')
    def pkgcontents(dbfilename):
        contents = list()
        fd = open(dbfilename)
        for line in fd:
            line = line.replace('\n', '') 
            try:
                contents.append(PortagePkgPart.parse_dbcontentsline(line))
            except NotImplementedError:
                pass
        fd.close()
        return contents
    def allpkgcontents_generator():
        for contentfile in contentfiles():
            for pkg in pkgcontents(contentfile):
                yield pkg
    files_to_check = set(files)
    pkgparts = list()
    allpkgcontents = allpkgcontents_generator()
    while len(files_to_check) > 0:
        try:
            pkgpart = allpkgcontents.next()
        except StopIteration:
            break
        if not pkgpart.path in files_to_check:
            continue
        if pkgpart.is_md5_unchanged_in_fs():
            pkgparts.append(pkgpart)
            files_to_check.discard(pkgpart.path)
    return pkgparts
        

files = set(['/etc/make.conf', '/etc/mplayer.conf', '/etc/host.conf', '/etc/irssi.conf', '/etc/gtk/gtkrc.az', 'dsfdsdfs'])
unchanged_files = set([part.path for part in get_pkgparts(files)])
for file in unchanged_files:
    print '%s unchanged' % file
for file in files.difference(unchanged_files):
    print '%s changed' % file

