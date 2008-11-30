#! /usr/bin/python
import unittest
from etcproposals import etcproposals_lib
from etcproposals.portage_stubs import PortageInterface
import os.path
import os

TESTCONFIGFILENAME = '/etc/etcproposalsTESTCONFIG'
TESTCONFIGPROPOSALFILENAME = '/etc/._cfg0000_etcproposalsTESTCONFIG'

BASECONTENT = """#  Header: dkljdfskjjkd      
1
2
3 testtesttest
4 testtesttest
5
6
7
8
9
10
11
12



13"""

MODCONTENT = """#  Header: fdskjkljfsdkjdsfkkj
1
2
3 testte---sttest
4 testtesttest
5
7
8
9
9a
10
11
12

13"""

class TestEtcProposalsLib(unittest.TestCase):
    def setUp(self):
        self._assure_etc_in_config_protect()
        self._assure_no_proposals()
        self._write_testfiles()

    def tearDown(self):
        self._clear_testfiles()

    def _assure_no_proposals(self):
        changes = [change for change in etcproposals_lib.EtcProposals().get_all_changes()]
        self.failUnless(len(changes) == 0, 'This test can only run if there are no proposals on your system.')
    
    def _assure_etc_in_config_protect(self):
        self.failUnless('/etc' in PortageInterface.get_config_protect('portage'), 'This test can only run if /etc is in CONFIG_PROTECT.')

    def _write_testfiles(self):
        open(TESTCONFIGFILENAME , 'w').write(BASECONTENT)
        open(TESTCONFIGPROPOSALFILENAME, 'w').write(MODCONTENT)
    
    def _has_filecontent(self, filename, content):
        return open(filename).read() == content

    def _clear_testfiles(self):
        for testfile in [TESTCONFIGPROPOSALFILENAME, TESTCONFIGFILENAME]:
            try:
                os.unlink(testfile)
            except OSError:
                pass


class TestUseAll(TestEtcProposalsLib):
    def runTest(self):
        """Testing if applying all changes works"""
        proposals = etcproposals_lib.EtcProposals()
        for change in proposals.get_all_changes():
            change.use()
        proposals.apply()
        self.failUnless(self._has_filecontent(TESTCONFIGFILENAME, MODCONTENT), 'Filecontent is wrong.')
        self.failIf(os.path.exists(TESTCONFIGPROPOSALFILENAME), 'Proposal wasnt removed.')

class TestZapAll(TestEtcProposalsLib):
    def runTest(self):
        """Testing if not applying all changes works"""
        proposals = etcproposals_lib.EtcProposals()
        for change in proposals.get_all_changes():
            change.zap()
        proposals.apply()
        self.failUnless(self._has_filecontent(TESTCONFIGFILENAME, BASECONTENT), 'Filecontent changed.')
        self.failIf(os.path.exists(TESTCONFIGPROPOSALFILENAME), 'Proposal wasnt removed.')

class TestUndoAll(TestEtcProposalsLib):
    def runTest(self):
        """Testing if undoing all changes works"""
        proposals = etcproposals_lib.EtcProposals()
        for change in proposals.get_all_changes():
            change.use()
        for change in proposals.get_all_changes():
            change.undo()
        proposals.apply()
        self.failUnless(self._has_filecontent(TESTCONFIGFILENAME, BASECONTENT), 'Filecontent changed.')
        self.failUnless(os.path.exists(TESTCONFIGPROPOSALFILENAME), 'Proposal was removed.')

class TestWhitespaceonly(TestEtcProposalsLib):
    def runTest(self):
        """Testing if whitespace recognition works"""
        proposals = etcproposals_lib.EtcProposals()
        whitespacechanges = [change for change in proposals.get_all_changes() if change.is_whitespace_only()]
        self.failUnless(len(whitespacechanges) == 1, 'Whitespace recognition failed.')

class TestCVSHeader(TestEtcProposalsLib):
    def runTest(self):
        """Testing if cvs header recognition works"""
        proposals = etcproposals_lib.EtcProposals()
        cvsheaderchanges = [change for change in proposals.get_all_changes() if change.is_cvsheader()]
        self.failUnless(len(cvsheaderchanges) == 1, 'CVS-Header recognition failed.')

class TestFileScan(TestEtcProposalsLib):
    def runTest(self):
        """Testing if scanning all config files for modifications (comparing to vdb) works"""
	etcproposals_lib.EtcProposals.scan_all_files()


alltests = [TestUseAll(), TestZapAll(), TestUndoAll(), TestWhitespaceonly(), TestCVSHeader(), TestFileScan()]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    #unittest.TextTestRunner(descriptions=10, verbosity=10).run(alltestssuite)
    unittest.main()
