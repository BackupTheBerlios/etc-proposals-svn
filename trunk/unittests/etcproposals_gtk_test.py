#! /usr/bin/python
import unittest
import pygtk
pygtk.require('2.0')
import gtk

from etcproposals.etcproposals_gtk2 import ScanFSWindow
from etcproposals.etcproposals_gtk2 import ChangeLabel
from etcproposals.etcproposals_gtk2 import ChangeContent
from etcproposals.etcproposals_gtk2 import EtcProposalChangeView
from etcproposals.etcproposals_gtk2 import EtcProposalsTreeView
from etcproposals.etcproposals_gtk2 import EtcProposalsChangesView
from etcproposals.etcproposals_gtk2 import EtcProposalsPanedView
from etcproposals.etcproposals_gtk2 import EtcProposalsView
from etcproposals.etcproposals_gtk2 import EtcProposalsController


class GUITestFailedError(Exception):
    pass


class EtcProposalChangeStub(object):
    def get_file_path(self):
        return '/etc/make.conf'
    def get_revision(self):
        return 0
    def __init__(self, value=True):
        self.value = value
        (self.touched, self.merge) = (False, False)
    def get_action(self):
        return 'insert'
    def get_affected_lines(self):
        return (2,5)
    def is_whitespace_only(self):
        return self.value
    def is_cvsheader(self):
        return self.value
    def is_unmodified(self):
        return self.value
    def use(self):
        (self.touched, self.merge) = (True, True)
    def zap(self):
        (self.touched, self.merge) = (True, False)
    def undo(self):
        (self.touched, self.merge) = (False, False)
    def get_base_content(self):
        return ['']
    def get_proposed_content(self):
        return ['proposed']
    def get_status(self):
        return 'undecided'


class EtcProposalsStub(list):
    def get_files(self):
        return ['/etc/make.conf', '/etc/issue']
    def get_whitespace_changes(self):
        return [EtcProposalChangeStub(True)]
    def get_cvsheader_changes(self):
        return [EtcProposalChangeStub(True)]
    def get_unmodified_changes(self):
        return [EtcProposalChangeStub(False)]
    def get_all_changes(self):
        return [EtcProposalChangeStub(True), EtcProposalChangeStub(False)]
    def warmup_cache(self):
        pass
    

class EtcProposalsControllerStub(object):
    def undo_changes(self, changes):
        pass
    def zap_changes(self, changes):
        pass
    def use_changes(self, changes):
        pass

class TestGtk(unittest.TestCase):
    def setUp(self):
        self.Failed = False
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.testbox = gtk.VBox(False, 0)
        box = gtk.HBox(False, 0)
        fail_button = gtk.Button('Test failed')
        fail_button.connect('clicked', lambda b: self.gtk_fail())
        passed_button = gtk.Button('Test passed')
        passed_button.connect('clicked', lambda b: self.gtk_passed())
        box.pack_start(fail_button, True, False, 1)
        box.pack_start(passed_button, True, False, 1)
        self.testbox.pack_end(box, False, False, 1)
        window.add(self.testbox)
        self.window = window
        fail_button.show()
        passed_button.show()
        box.show()
        self.testbox.show()
        window.show()

    def gtk_fail(self):
        self.window.destroy()
        gtk.main_quit()
        self.Failed = True
    
    def gtk_passed(self):
        self.window.destroy()
        gtk.main_quit()


class TestScanFSWindow(TestGtk):
    def runTest(self):
        """Testing the wait window """
        wait_win = ScanFSWindow()
        wait_win.current_file = "/etc/fstab"
        gtk.main()
        wait_win.destroy()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeLabel(TestGtk):
    def runTest(self):
        """Testing GTK display of change label"""
        change = EtcProposalChangeStub()
        controller = EtcProposalsControllerStub()
        label = ChangeLabel(change, controller)
        self.testbox.pack_start(label, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeContent(TestGtk):
    def runTest(self):
        """Testing GTK display of a change"""
        change = EtcProposalChangeStub()
        contentGTK = ChangeContent(change)
        self.testbox.pack_start(contentGTK, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')
    

class TestChangeView(TestGtk):
    def runTest(self):
        """Testing GTK display of a change"""
        change = EtcProposalChangeStub()
        controller = EtcProposalsControllerStub()
        changeGTK = EtcProposalChangeView(change, controller)
        self.testbox.pack_start(changeGTK, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestTreeView(TestGtk):
    def runTest(self):
        """Testing GTK display of proposals"""
        proposals = EtcProposalsStub()
        controller = EtcProposalsControllerStub()
        tv = EtcProposalsTreeView(proposals, controller)
        self.testbox.pack_start(tv, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangesView(TestGtk):
    def runTest(self):
        """Testing GTK display of changes"""
        changes = list()
        controller = EtcProposalsControllerStub()
        changes.append(EtcProposalChangeStub())
        changes.append(EtcProposalChangeStub())
        changes.append(EtcProposalChangeStub())
        changesview = EtcProposalsChangesView(controller)
        changesview.update_changes(lambda: changes)
        changesview.show_all()
        self.testbox.pack_start(changesview, True, True, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestPanedView(TestGtk):
    def runTest(self):
        """Testing GTK paned"""
        proposals = EtcProposalsStub()
        controller = EtcProposalsControllerStub()
        view = EtcProposalsPanedView(proposals, controller)
        self.testbox.pack_start(view, True, True, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestView(TestGtk):
    def runTest(self):
        """Testing GTK display"""
        proposals = EtcProposalsStub()
        controller = EtcProposalsControllerStub()
        self.view = EtcProposalsView(proposals, controller)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')

    def gtk_passed(self):
        self.view.destroy()
        TestGtk.gtk_passed(self)
        
    def gtk_failed(self):
        self.view.destroy()
        TestGtk.gtk_failed(self)


class TestController(TestGtk):
    def runTest(self):
        """Testing GTK controller"""
        proposals = EtcProposalsStub()
        self.controller = EtcProposalsController(proposals)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')

    def gtk_passed(self):
        self.controller.view.destroy()
        TestGtk.gtk_passed(self)
        
    def gtk_failed(self):
        self.controller.view.destroy()
        TestGtk.gtk_failed(self)


alltests = [TestScanFSWindow(), TestChangeLabel(), TestChangeContent(), TestChangeView(), TestTreeView(), TestChangesView(), TestPanedView(), TestView(), TestController()]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    unittest.TextTestRunner(descriptions=10, verbosity=10).run(alltestssuite)
