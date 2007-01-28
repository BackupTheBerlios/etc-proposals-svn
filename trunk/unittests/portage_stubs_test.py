#! /usr/bin/python
import unittest
from etcproposals.portage_stubs import PortageInterface
import portage

class TestPortageStubs(unittest.TestCase):
    def test_get_md5_from_vdb(self):
        nonexsistantfile = '/some nonexsistant file'
        issue = '/etc/issue'
        hostname = '/etc/conf.d/hostname'
        files = set([issue, hostname, nonexsistantfile])
        md5s = PortageInterface.get_md5_from_vdb(files)
        self.failIf(md5s.has_key(nonexsistantfile), 'Found an entry in the pkgdb that shouldnt be there: "%s".' % nonexsistantfile )
        self.failIf(not md5s.has_key(issue), 'Didnt find an entry in the pkgdb: "%s"' % issue)
        self.failIf(not md5s.has_key(hostname), 'Didnt find an entry in the pkgdb: "%s"' % hostname)
    
    def test_get_config_protect(self):
        portage_config_protect = set(portage.settings['CONFIG_PROTECT'].split(' '))
        stubs_config_protect = set(PortageInterface.get_config_protect())
        self.failIf(not stubs_config_protect == portage_config_protect, 'Calculated CONFIG_PROTECT differs from the one calculated by portage.')

if __name__ == '__main__':
    unittest.main()
