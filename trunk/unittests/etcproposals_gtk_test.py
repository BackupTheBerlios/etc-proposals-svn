#! /usr/bin/python
import unittest
import pygtk
pygtk.require('2.0')
import gtk
from etcproposals.etcproposals_gtk import EtcProposalChangeTypeGtk


class GUITestFailedError(Exception):
    pass

class EtcProposalsChangeStub(object):
    def __init__(self, value=True):
        self.value = value
    def is_whitespace_only(self):
        return self.value
    def is_cvsheader(self):
        return self.value
    def is_unchanged(self):
        return self.value

class TestGtk(unittest.TestCase):
    def setUp(self):
        self.Failed = False
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect('destroy', lambda w: gtk.main_quit())
        self.testbox = gtk.VBox(False, 0)
        box = gtk.HBox(False, 0)
        fail_button = gtk.Button('Test failed')
        fail_button.connect('clicked', lambda w: self.gtk_fail())
        passed_button = gtk.Button('Test passed')
        passed_button.connect('clicked', lambda w: gtk.main_quit())
        box.pack_start(fail_button, True, False, 1)
        box.pack_start(passed_button, True, False, 1)
        fail_button.show()
        passed_button.show()
        box.show()
        self.testbox.show()
        window.show()
        self.testbox.pack_end(box, False, False, 1)
        window.add(self.testbox)

    def gtk_fail(self):
        gtk.main_quit()
        self.Failed = True


class TestChangeTypeGtk(TestGtk):
    def runTest(self):
    	"""Testing GTK display of changestatus"""
        false_change = EtcProposalsChangeStub(False)
        true_change = EtcProposalsChangeStub()
        true_row = EtcProposalChangeTypeGtk(true_change)
        false_row = EtcProposalChangeTypeGtk(false_change)
        self.testbox.pack_start(false_row, False, False, 1)
        self.testbox.pack_start(true_row, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


alltests = [TestChangeTypeGtk()]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    unittest.main()
