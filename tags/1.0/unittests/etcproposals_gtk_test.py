#! /usr/bin/python
import unittest
import pygtk
pygtk.require('2.0')
import gtk
from etcproposals.etcproposals_gtk import EtcProposalChangeType
from etcproposals.etcproposals_gtk import EtcProposalChangeTitle
from etcproposals.etcproposals_gtk import EtcProposalChangeLabel
from etcproposals.etcproposals_gtk import EtcProposalChangeStatus
from etcproposals.etcproposals_gtk import EtcProposalsChangeView
from etcproposals.etcproposals_gtk import EtcProposalChangeContent
from etcproposals.etcproposals_gtk import EtcProposalsTreeView
from etcproposals.etcproposals_gtk import EtcProposalsChangesView
from etcproposals.etcproposals_gtk import EtcProposalsPanedView
from etcproposals.etcproposals_gtk import EtcProposalsView
from etcproposals.etcproposals_gtk import EtcProposalsController


class GUITestFailedError(Exception):
    pass


class EtcProposalsChangeStub(object):
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


class EtcProposalsStub(object):
    def get_files(self):
        return ['/etc/make.conf', '/etc/issue']
    def get_whitespace_changes(self):
        return [EtcProposalsChangeStub(True)]
    def get_cvsheader_changes(self):
        return [EtcProposalsChangeStub(True)]
    def get_unmodified_changes(self):
        return [EtcProposalsChangeStub(False)]
    def get_all_changes(self):
        return [EtcProposalsChangeStub(True), EtcProposalsChangeStub(False)]
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
        

class TestChangeType(TestGtk):
    def runTest(self):
        """Testing GTK display of change type"""
        false_change = EtcProposalsChangeStub(False)
        true_change = EtcProposalsChangeStub()
        true_type = EtcProposalChangeType(true_change)
        false_type = EtcProposalChangeType(false_change)
        self.testbox.pack_start(false_type, False, False, 1)
        self.testbox.pack_start(true_type, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')
    

class TestChangeTitle(TestGtk):
    def runTest(self):
        """Testing GTK display of change title"""
        change = EtcProposalsChangeStub()
        titlelabel = EtcProposalChangeTitle(change)
        self.testbox.pack_start(titlelabel, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeStatus(TestGtk):
    def runTest(self):
        """Testing GTK display of change status"""
        change = EtcProposalsChangeStub()
        controller = EtcProposalsControllerStub()
        changestatus = EtcProposalChangeStatus(change, controller)
        self.testbox.pack_start(changestatus, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeLabel(TestGtk):
    def runTest(self):
        """Testing GTK display of change label"""
        change = EtcProposalsChangeStub()
        controller = EtcProposalsControllerStub()
        label = EtcProposalChangeLabel(change, controller)
        self.testbox.pack_start(label, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangeContent(TestGtk):
    def runTest(self):
        """Testing GTK display of a change"""
        change = EtcProposalsChangeStub()
        contentGTK = EtcProposalChangeContent(change)
        self.testbox.pack_start(contentGTK, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')
    

class TestChangeView(TestGtk):
    def runTest(self):
        """Testing GTK display of a change"""
        change = EtcProposalsChangeStub()
        controller = EtcProposalsControllerStub()
        changeGTK = EtcProposalsChangeView(change, controller)
        self.testbox.pack_start(changeGTK, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestTreeView(TestGtk):
    def runTest(self):
        """Testing GTK display of proposals"""
        proposals = EtcProposalsStub()
        tv = EtcProposalsTreeView(proposals)
        self.testbox.pack_start(tv, False, False, 1)
        gtk.main()
        self.failIf(self.Failed, 'Test failed.')


class TestChangesView(TestGtk):
    def runTest(self):
        """Testing GTK display of changes"""
        changes = list()
        controller = EtcProposalsControllerStub()
        changes.append(EtcProposalsChangeStub())
        changes.append(EtcProposalsChangeStub())
        changes.append(EtcProposalsChangeStub())
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


alltests = [TestChangeType(), TestChangeTitle(), TestChangeStatus(), TestChangeLabel(), TestChangeContent(), TestChangeView(), TestTreeView(), TestChangesView(), TestPanedView(), TestView(), TestController()]
alltestssuite = unittest.TestSuite(alltests)

if __name__ == '__main__':
    unittest.TextTestRunner(descriptions=10, verbosity=10).run(alltestssuite)
