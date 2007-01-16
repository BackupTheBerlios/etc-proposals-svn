#! /usr/bin/python

import os, os.path, datetime, md5, pprint

VDB_PATH = "/var/db/pkg/"

class NotImplementedError(Exception):
    pass


class PortagePkgFile(object):
    @staticmethod
    def parse_dbcontentsline(dbcontentsline):
        if dbcontentsline.startswith('obj'):
            return PortagePkgFileObject(dbcontentsline)
        else:
            raise NotImplementedError


class PortagePkgFileObject(PortagePkgFile):
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
        
def check_file_md5s(files):
    def contentfiles():
        return  (os.path.join(path, file)
            for (path, dirs, files) in os.walk(VDB_PATH) for file in files
            if file == 'CONTENTS')
    def filelines(file):
        fd = open(file)
        lines = [line.replace('\n', '') for line in fd.readlines()]
        fd.close()
        return lines
    def pkgcontents(file):
        contents = list()
        for line in filelines(file):
            try:
                contents.append(PortagePkgFile.parse_dbcontentsline(line))
            except NotImplementedError:
                pass
        return contents
    def allpkgcontents_generator():
        for contentfile in contentfiles():
            for pkg in pkgcontents(contentfile):
                yield pkg
    files_to_check = set(files)
    checked_files = dict()
    allpkgcontents = allpkgcontents_generator()
    while len(files_to_check) > 0:
        try:
            pkg = allpkgcontents.next()
        except StopIteration:
            break
        if not pkg.path in files_to_check:
            continue
        if pkg.is_md5_unchanged_in_fs():
            checked_files[pkg.path] = pkg.md5
        else:
            checked_files[pkg.path] = None
        files_to_check.discard(pkg.path)
    for file in files_to_check:
        checked_files[file] = None
    pprint.pprint(checked_files)
        

        
    
check_file_md5s(['/etc/make.conf', '/etc/mplayer.conf', '/etc/host.conf', '/etc/irssi.conf', '/etc/gtk/gtkrc.az', 'dsfdsdfs'] )
#
#
#
#content_files = (os.path.join(path, file)
#   for (path, dirs, files) in os.walk(VDB_PATH) for file in files
#   if file == 'CONTENTS')
#
#
#etcpkgfiles = []
#for content_filenname in content_files:
#   content_file = open(content_filenname)
#   for line in content_file.readlines():
#       try:
#           line = line.replace('\n','')
#           pkgfile = PortagePkgFile.parse_dbcontentsline(line)
#           if pkgfile.path.startswith('/etc/'):
#               etcpkgfiles.append(pkgfile)
#       except NotImplementedError:
#           pass
#
#print 'unchanged:'
#unchangedetcfiles = [pkgfile for pkgfile in etcpkgfiles if pkgfile.is_unchanged_in_fs()]
#for file in unchangedetcfiles:
#   print file.path
#print 'changed:'
#for file in etcpkgfiles:
#   if not file in unchangedetcfiles: 
#       print file.path
