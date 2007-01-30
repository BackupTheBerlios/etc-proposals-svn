#! /usr/bin/python
import unittest
from etcproposals.portage_stubs import PortageInterface
import portage

class Test_get_md5_from_vdb(unittest.TestCase):
    def runTest(self):
        """Testing vdb access"""
        nonexsistantfile = '/some nonexsistant file'
        issue = '/etc/issue'
        hostname = '/etc/conf.d/hostname'
        files = set([issue, hostname, nonexsistantfile])
        md5s = PortageInterface.get_md5_from_vdb(files)
        self.failIf(md5s.has_key(nonexsistantfile), 'Found an entry in the pkgdb that shouldnt be there: "%s".' % nonexsistantfile )
        self.failUnless(md5s.has_key(issue), 'Didnt find an entry in the pkgdb: "%s"' % issue)
        self.failUnless(md5s.has_key(hostname), 'Didnt find an entry in the pkgdb: "%s"' % hostname)
    
class Test_get_config_protect(unittest.TestCase):
    def runTest(self):
        """Testing CONFIG_PROTECT calculation"""
        portage_config_protect = set(portage.settings['CONFIG_PROTECT'].split(' '))
        stubs_config_protect = set(PortageInterface.get_config_protect())
        self.failUnless(stubs_config_protect == portage_config_protect, 'Calculated CONFIG_PROTECT differs from the one calculated by portage.')

alltests = [Test_get_config_protect(), Test_get_md5_from_vdb()]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    unittest.main()
