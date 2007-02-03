#! /usr/bin/python
import unittest
import pygtk
pygtk.require('2.0')
import gtk
from etcproposals.etcproposals_gtk import EtcProposalChangeTypeGtk
from etcproposals.etcproposals_gtk import EtcProposalChangeTitleGtk
from etcproposals.etcproposals_gtk import EtcProposalChangeLabelGtk
from etcproposals.etcproposals_gtk import EtcProposalChangeStatusGtk
from etcproposals.etcproposals_gtk import EtcProposalChangeDecoratorGtk


class GUITestFailedError(Exception):
    pass

class EtcProposalsChangeStub(object):
    def get_file_path(self):
        return '/etc/make.conf'
    def get_revision(self):
        return 0
    def __init__(self, value=True):
        self.value = value
        self.opcode = ['insert', 2, 5, 2, 2]
        (self.touched, self.merge) = (False, False)
    def is_whitespace_only(self):
        return self.value
    def is_cvsheader(self):
        return self.value
    def is_unchanged(self):
        return self.value
    def use(self):
        (self.touched, self.merge) = (True, True)
    def zap(self):
        (self.touched, self.merge) = (True, False)
    def undo(self):
        (self.touched, self.merge) = (False, False)
        

class TestGtk(unittest.TestCase):
    def setUp(self):
        self.Failed = False
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.testbox = gtk.VBox(False, 0)
        box = gtk.HBox(False, 0)
        fail_button = gtk.Button('Test failed')
        fail_button.connect('clicked', lambda w: self.gtk_fail())
        passed_button = gtk.Button('Test passed')
        passed_button.connect('clicked', lambda w: self.gtk_passed())
        box.pack_start(fail_button, True, False, 1)
        box.pack_start(passed_button, True, False, 1)
        fail_button.show()
        passed_button.show()
        box.show()
        self.testbox.show()
        window.show()
        self.testbox.pack_end(box, False, False, 1)
        window.add(self.testbox)
        self.window = window

    def gtk_fail(self):
        self.window.destroy()
        gtk.main_quit()
        self.Failed = True
    
    def gtk_passed(self):
        self.window.destroy()
        gtk.main_quit()
        

class TestChangeTypeGtk(TestGtk):
    def runTest(self):
        """Testing GTK display of change type"""
        false_change = EtcProposalsChangeStub(False)
        true_change = EtcProposalsChangeStub()
        true_type = EtcProposalChangeTypeGtk(true_change)
        false_type = EtcProposalChangeTypeGtk(false_change)
        self.testbox.pack_start(false_type, False, False, 1)
        self.testbox.pack_start(true_type, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')
    

class TestChangeTitleGtk(TestGtk):
    def runTest(self):
        """Testing GTK display of change title"""
        change = EtcProposalsChangeStub()
        titlelabel = EtcProposalChangeTitleGtk(change)
        self.testbox.pack_start(titlelabel, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeStatusGtk(TestGtk):
    def runTest(self):
        """Testing GTK display of change status"""
        change = EtcProposalsChangeStub()
        changestatus = EtcProposalChangeStatusGtk(change)
        self.testbox.pack_start(changestatus, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeLabelGtk(TestGtk):
    def runTest(self):
        """Testing GTK display of change title"""
        change = EtcProposalsChangeStub()
        label = EtcProposalChangeLabelGtk(change)
        self.testbox.pack_start(label, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeDecoratorGtk(TestGtk):
    def runTest(self):
        """Testing GTK display of a change"""
        change = EtcProposalsChangeStub()
        changeGTK = EtcProposalChangeDecoratorGtk(change)
        self.testbox.pack_start(changeGTK, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')

alltests = [TestChangeTypeGtk(), TestChangeTitleGtk(), TestChangeStatusGtk(), TestChangeLabelGtk(), TestChangeDecoratorGtk()]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    unittest.main()
