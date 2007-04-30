#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Wickersheimer Jeremy, Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a qt4-frontend to integrate modified configs, post-emerge

__author__ = 'Wickersheimer Jeremy'
__version__ = '1.0'
__date__ = '2007-03-18'
__doc__ = """
etcproposals_qt4 is a qt4-frontend to integrate modified configs, post-emerge.
Its implemented using the MVC (model-view-controller) design pattern.

The model is represented by the EtcProposalsGtkDecorator class, whose functionality
is mostly implemented in etcproposals_lib.

The view is implemented by the EtcProposalsView using most of the other helper classes
in this module to show a representation of the model and accept user input.

The controller is implemented by the EtcProposalsController and is used to modify the
model while keeping the view in sync.

Here is a bit of ASCII-art showing the hierachy of objects in the view:
EtcProposalsView (window)
+- (toolbar) -> starts AboutDialog, HelpDialog
+- EtcProposalsPanedView
   +- EtcProposalsTreeView
   +- EtcProposalsChangesView
      +- EtcProposalChangeView (multiple)
         +- ChangeLabel
         +- ChangeContent
"""
from etcproposals.etcproposals_lib import *
from etcproposals.etcproposals_lib import __version__ as __libversion__
import os, subprocess

try:
    import PyQt4.Qt as qt
except ImportError:
    raise FrontendFailedException('Could not find qt4-bindings.')


class KdelibsUtils(object):
    ICONDIR_PATHS = subprocess.Popen("kde-config --path icon", shell=True, stdout=subprocess.PIPE).stdout.readline().split(':')
    THEME = 'crystalsvg'
    ICONSIZE = '22x22'
    IMAGEFORMAT = 'png'

    @staticmethod
    def get_iconpath(category, iconname):
        pathend = os.path.join(KdelibsUtils.THEME, KdelibsUtils.ICONSIZE, category, iconname + '.' + KdelibsUtils.IMAGEFORMAT)
        for pathstart in KdelibsUtils.ICONDIR_PATHS:
            path = os.path.join(pathstart, pathend)
            if os.access(path, os.R_OK):
                return path
        raise LookupError, 'Icon %s not found.' % iconname


class EtcProposalsQt4Decorator(EtcProposals):
    """decoration of EtcProposals to satisfy the performance needs of the GUI"""
    def warmup_cache(self):
        """for the GUI,  we need to keep the cache warm"""
        self.get_whitespace_changes()
        self.get_cvsheader_changes()
        self.get_unmodified_changes()
        self.get_used_changes()
        self.get_zapped_changes()
        
	self.get_undecided_changes()


class EtcProposalsConfigQt4Decorator(EtcProposalsConfig):
    """stub to handle configuration settings for the Qt4 GUI"""
    pass


class ChangeLabel(qt.QFrame):
    """ChangeLabel is a widget showing all data of an
    EtcProposalsChange but the content. It contains an ChangeStatus,
    an ChangeTitle and an ChangeType."""

    class ChangeType(qt.QFrame):
        """ChangeType is a widget showing if a connected
        EtcProposalChange is Whitespace-Only, a CVS-Header or part of an Unmodified
        file"""
        def __init__(self, parent, change):
            qt.QFrame.__init__(self, parent)
            self.layout = qt.QHBoxLayout(self)
            self.labelstatus = [
                change.is_whitespace_only,
                change.is_cvsheader,
                change.is_unmodified ]
            self.setup_labels()
            self.update_change()
            self.show()

        def setup_labels(self):
            self.labels = map(lambda x: qt.QLabel(self), xrange(3))
            [label.show() for label in self.labels]
            [self.layout.addWidget(label) for label in self.labels]

        def update_change(self):
            for (label, status, text) in zip(self.labels, self.labelstatus, self.labeltexts()):
                if status():
                    label.setText(text)
                else:
                    label.setText('')

        @staticmethod
        def labeltexts():
            return ['whitespace', 'cvs-header', 'unchanged']

    class ChangeTitle(qt.QFrame):
        """ChangeTitle is a widget showing the filename, effected lines
        and proposal number of a connected EtcProposalsChange"""
        def __init__(self, parent, change):
            qt.QFrame.__init__(self, parent)
            self.layout = qt.QVBoxLayout(self)
            self.change = change
            self.filenamelabel = qt.QLabel(self)
            self.proposallabel = qt.QLabel(self)
            self.lineslabel = qt.QLabel(self)
            self.proposallinesbox = qt.QFrame(self)
            self.proposallinesboxlayout = qt.QHBoxLayout(self.proposallinesbox)
            self.layout.addWidget(self.filenamelabel)
            self.layout.addWidget(self.proposallinesbox)
            self.proposallinesboxlayout.addWidget(self.proposallabel)
            self.proposallinesboxlayout.addWidget(self.lineslabel)
            self.update_change()
            for control in [self.filenamelabel, self.proposallabel, self.lineslabel, self.proposallinesbox, self]:
                control.show()

        def update_change(self):
            self.filenamelabel.setText(self.change.get_file_path())
            self.proposallabel.setText('Proposal: %s' % self.change.get_revision())
            self.lineslabel.setText('Lines: %d-%d' % self.change.get_affected_lines())

    class ChangeStatus(qt.QFrame):
        """ChangeStatus is a widget showing if a connected
        EtcProposalsChange is selected to be used or zapped. The user can change
        the status of the EtcProposalsChange using the toggle buttons. The
        ChangeStatus uses an EtcProposalsController to change the
        status."""
        def __init__(self,parent, change, controller):
            qt.QFrame.__init__(self, parent)
            self.layout = qt.QHBoxLayout(self)
            self.controller = controller
            self.change = change
            self.updating = False
            self.usebutton = qt.QPushButton('Use', self)
            self.zapbutton = qt.QPushButton('Zap', self)
            self.usebutton.setCheckable(True)
            self.zapbutton.setCheckable(True)
            self.buttons = qt.QButtonGroup(self)
            self.buttons.setExclusive(False)
            self.buttons.addButton(self.usebutton)
            self.buttons.addButton(self.zapbutton)
            self.layout.addWidget(self.usebutton)
            self.layout.addWidget(self.zapbutton)
            self.connect(self.buttons, qt.SIGNAL('buttonClicked(QAbstractButton *)'), self.button_toggled)
            self.update_change()
            self.show()

        def update_change(self):
            buttonstates = (False, False)
            if self.change.touched:
                if self.change.merge:
                    buttonstates = (True, False)
                else:
                    buttonstates = (False, True)
            self.updating = True;
            self.usebutton.setChecked(buttonstates[0])
            self.zapbutton.setChecked(buttonstates[1])
            self.updating = False

        def button_toggled(self, clicked):
            if not self.updating:
                if self.usebutton.isChecked():
                    if clicked != self.usebutton:
                        self.usebutton.setChecked(False)
                    else:
                        self.zapbutton.setChecked(False)
                        self.controller.use_changes([self.change])
                elif self.zapbutton.isChecked():
                    self.usebutton.setChecked(False)
                    self.controller.zap_changes([self.change])
                else:
                    self.controller.undo_changes([self.change])


    def __init__(self, parent, change, controller):
        qt.QFrame.__init__(self, parent)
        self.setFrameStyle(qt.QFrame.StyledPanel | qt.QFrame.Raised)
        self.change = change
        self.title = ChangeLabel.ChangeTitle(self, change)
        self.type = ChangeLabel.ChangeType(self, change)
        self.status = ChangeLabel.ChangeStatus(self, change, controller)
        self.layout = qt.QHBoxLayout(self)
        self.layout.addWidget(self.status)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.type)
        self.show()

    def update_change(self):
        for control in [self.title, self.type]:
            control.update_change()


class ChangeContent(qt.QFrame):
    """ChangeContent is a widget showing the modified lines of an
    EtcProposalsChange"""
    def __init__(self, parent, change):
        qt.QFrame.__init__(self, parent)
        self.layout = qt.QVBoxLayout(self)
        self.change = change
        self.header = qt.QLabel(self)
        self.removetextview = qt.QTextEdit(self)
        self.inserttextview = qt.QTextEdit(self)
        self.removetextview.setTextColor(qt.QColor(255, 60, 60))
        self.inserttextview.setTextColor(qt.QColor(10, 255, 10))
        for textview in [self.removetextview, self.inserttextview]:
            textview.setReadOnly(True)
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.removetextview)
        self.layout.addWidget(self.inserttextview)
        self.header.show()
        self.update_change()
        self.show()

    def update_change(self):
        action = self.change.get_action()
        affected_lines = self.change.get_affected_lines()
        headertext = '%s content at lines %d-%d in the file %s' % (
            action,
            affected_lines[0],
            affected_lines[1],
            self.change.get_file_path())
        self.header.setText(headertext)
        for textview in [self.removetextview, self.inserttextview]:
            textview.hide()
        if action in ['delete', 'replace']:
            self.removetextview.show()
        if action in ['insert', 'replace']:
            self.inserttextview.show()
        self.removetextview.setPlainText(''.join(self.change.get_base_content())[:-1])
        self.inserttextview.setPlainText(''.join(self.change.get_proposed_content())[:-1])


class EtcProposalsChangeView(qt.QFrame):
    """EtcProposalChangeView is an widget showing everything about an
    EtcProposalsChange and allows to change its status. It contains an
    ChangeLabel and an ChangeContent. In all, it contains the following objects:
     - ChangeLabel
     - ChangeContent"""
    def __init__(self, parent, change, controller):
        qt.QFrame.__init__(self, parent)
        self.layout = qt.QVBoxLayout(self)
        self.change = change
        self.label = qt.QLabel(self.get_labeltext(), self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(ChangeLabel(self, change, controller))
        self.layout.addWidget(ChangeContent(self, change))

    def get_labeltext(self):
        affected_lines = self.change.get_affected_lines()
        return '%s:%s-%s(%d)' % (self.change.get_file_path(), affected_lines[0], affected_lines[1], self.change.get_revision())


class EtcProposalsTreeView(qt.QFrame):
    """EtcProposalsTreeView implements the Treeview for selecting files and changes."""
    def __init__(self, parent, proposals):
        qt.QFrame.__init__(self, parent)
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
        self.layout = qt.QVBoxLayout(self)
        self.layout.setMargin(0)
        self.treeview = qt.QTreeWidget(self)
        self.treeview.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding))
        self.treeview.setColumnCount(1)
        self.treeview.setHeaderLabel(self.tr("Proposals"))
        self.treeview.header().hide()
        # add top item
        self.fsnode = qt.QTreeWidgetItem(self.treeview)
        self.fsnode.setText(0, self.tr("Filesystem"))
        # add top item
        self.typenode = qt.QTreeWidgetItem(self.treeview)
        self.typenode.setText(0, self.tr("Type"))
        self.type_whitespace = qt.QTreeWidgetItem(self.typenode)
        self.type_whitespace.setText(0, self.tr("Whitespace"))
        self.type_cvs = qt.QTreeWidgetItem(self.typenode)
        self.type_cvs.setText(0, self.tr("CVS-Header"))
        self.type_unmodified = qt.QTreeWidgetItem(self.typenode)
        self.type_unmodified.setText(0, self.tr("Unmodified"))
        self.typenode.setExpanded(True)
        # add top item
        self.statusnode = qt.QTreeWidgetItem(self.treeview)
        self.statusnode.setText(0, self.tr("Status"))
        self.status_use = qt.QTreeWidgetItem(self.statusnode)
        self.status_use.setText(0, self.tr("Use"))
        self.status_zap = qt.QTreeWidgetItem(self.statusnode)
        self.status_zap.setText(0, self.tr("Zap"))
        self.status_undecided = qt.QTreeWidgetItem(self.statusnode)
        self.status_undecided.setText(0, self.tr("Undecided"))
        self.statusnode.setExpanded(True)
        # add treeview to layout
        self.layout.addWidget(self.treeview)
        # set context menu
        self.menu = qt.QMenu(self)
        self.setContextMenuPolicy(qt.Qt.CustomContextMenu)
        self.connect(self, qt.SIGNAL("customContextMenuRequested(const QPoint &)"), self.contextMenu)
        self.proposals = proposals
        self.refresh()
        self.show()

    # implement QWidget.sizeHint so the QSplitter can give a reasonable default size
    def sizeHint(self):
        return qt.QSize(100, 300)

    def contextMenu(self, point):
        item = self.treeview.itemAt(point)
        if item is not None:
            self.menu.popup(self.cursor().pos())

    def refresh(self):
        childcount = self.fsnode.childCount()
        for i in range(0,childcount):
            filenode = self.fsnode.takeChild(i)
        for file in self.proposals.get_files():
            newnode = qt.QTreeWidgetItem(self.fsnode)
            newnode.setText(0, file)
        self.fsnode.setExpanded(True)

    def get_changegenerator_for_node(self, nodes):
        if len(nodes) == 0:
            return None
        elif nodes[0] == self.status_use:
            return self.proposals.get_used_changes
        elif nodes[0] == self.status_zap:
            return self.proposals.get_zapped_changes
        elif nodes[0] == self.status_undecided:
            return self.proposals.get_undecided_changes
        elif nodes[0] == self.type_whitespace:
            return self.proposals.get_whitespace_changes
        elif nodes[0] == self.type_cvs:
            return self.proposals.get_cvsheader_changes
        elif nodes[0] == self.type_unmodified:
            return self.proposals.get_unmodified_changes
        elif nodes[0] == self.status_use:
            return self.proposals.get_used_changes
        else:
            if nodes[0].parent() == self.fsnode:
                file = nodes[0].text(0)
                return lambda: self.proposals.get_file_changes(file)
            else:
                return lambda: []


class EtcProposalsChangesView(qt.QFrame):
    """EtcProposalsChangesView implements the display a list of changes. It
    uses EtcProposalChangeViews to display the changes. The changes it
    displays are provided by a functor."""
    def __init__(self, parent, controller):
        qt.QFrame.__init__(self, parent)
        self.controller = controller
        self.changes_generator = lambda: []
        self.expanded_changes = set()
        self.layout = qt.QVBoxLayout(self)
        self.changeList = list()
        self.show()

    # implement QWidget.sizeHint so the QSplitter can give a reasonable default size
    def sizeHint(self):
        return qt.QSize(300, 300)

    def update_changes(self, changes_generator = None):
        self.hide()
        # remove all items
        while len(self.changeList) > 0:
            i = self.changeList.pop()
            i.hide()
            self.layout.removeWidget(i)
        if not changes_generator == None:
            self.changes_generator = changes_generator
        for change in self.changes_generator():
            changeview = EtcProposalsChangeView(self, change, self.controller)
            self.changeList.append(changeview)
            self.layout.addWidget(changeview)
            changeview.show()
        self.show()

    # TODO:
    #def collapse_all(self):
        #[child.set_expanded(False) for child in self.get_children()]
    
    # TODO:
    #def expand_all(self):
        #[child.set_expanded(True) for child in self.get_children()]


class EtcProposalsPanedView(qt.QSplitter):
    """EtcProposalsPanedView is a Panel containing an EtcProposalsTreeView for
    selecting sets of changes and an EtcProposalsChangesView to display
    them."""
    def __init__(self, parent, proposals, controller):
        qt.QSplitter.__init__(self, qt.Qt.Horizontal, parent)
        self.controller = controller
        self.proposals = proposals
        self.changesview = EtcProposalsChangesView(self, self.controller)
        self.treeview = EtcProposalsTreeView(self, self.proposals)
        self.tv_scrollwindow = qt.QScrollArea(self)
        self.cv_scrollwindow = qt.QScrollArea(self)
        self.tv_scrollwindow.setWidget(self.treeview)
        self.cv_scrollwindow.setWidget(self.changesview)
        self.tv_scrollwindow.setWidgetResizable(True)
        self.cv_scrollwindow.setWidgetResizable(True)
        self.treeview.connect(self.treeview.treeview, qt.SIGNAL("itemSelectionChanged()"), self.on_tv_item_selected)
        self.treeview.menu.addAction(self.tr("Use All"), self.on_use_tv_menu_select)
        self.treeview.menu.addAction(self.tr("Zap All"), self.on_zap_tv_menu_select)
        self.treeview.menu.addAction(self.tr("Undo All"), self.on_undo_tv_menu_select)
        self.tv_scrollwindow.show()
        self.cv_scrollwindow.show()

    def on_tv_item_selected(self):
        changegenerator = self.treeview.get_changegenerator_for_node(self.treeview.treeview.selectedItems())
        if changegenerator == None:
            return False
        self.changesview.update_changes(changegenerator)
        return True

    def on_use_tv_menu_select(self):
        self.controller.use_changes(self.treeview.get_changegenerator_for_node(self.treeview.treeview.selectedItems())())

    def on_zap_tv_menu_select(self):
        self.controller.zap_changes(self.treeview.get_changegenerator_for_node(self.treeview.treeview.selectedItems())())

    def on_undo_tv_menu_select(self):
        self.controller.undo_changes(self.treeview.get_changegenerator_for_node(self.treeview.treeview.selectedItems())())


class HelpDialog(object):
    """Shows a short help text"""
    # TODO: write qt4 version
    pass


class AboutDialog(object):
    """AboutDialog just is an About Dialog"""
    # TODO: write qt4 version
    pass


class EtcProposalsView(qt.QMainWindow):
    """EtcProposalsView is a the Window that displays all the changes. It
    contains a EtcProposalsPanedView and an additional toolbar."""
    def __init__(self, proposals, controller):
        qt.QMainWindow.__init__(self)
        #etc-proposals controller
        self.controller = controller
        self.proposals = proposals
        self.setWindowTitle("QT4 etc-proposals")
        self.setGeometry(0,0,800,600)
        # define actions
        self.initActions()
        # build the menu
        self.initMenus()
        # init the tool bar
        self.initToolBar()
        # init the widgets
        self.initWidgets()
        # statusBar
        #self.initStatusBar()
        self.show()

    def initActions(self):
        #Exit
        self.exitAct = qt.QAction(self.tr("E&xit"), self)
        self.exitAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'exit')))
        self.exitAct.setShortcut(self.tr("Ctrl+Q"))
        self.exitAct.setStatusTip(self.tr("Exit the application"))
        self.connect(self.exitAct, qt.SIGNAL("triggered()"), self.slotExit)
        #Apply
        self.applyAct = qt.QAction(self.tr("A&pply"), self)
        self.applyAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'button_ok')))
        self.applyAct.setStatusTip(self.tr("Apply selected changes"))
        self.connect(self.applyAct, qt.SIGNAL("triggered()"), self.slotApply)
        #Refresh
        self.refreshAct = qt.QAction(self.tr("R&efresh"), self)
        self.refreshAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'reload')))
        self.refreshAct.setStatusTip(self.tr("Refresh proposals"))
        self.connect(self.refreshAct, qt.SIGNAL("triggered()"), self.slotRefresh)
        #Collapse
        self.collapseAct = qt.QAction(self.tr("C&ollapse"), self)
        self.collapseAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'add')))
        self.collapseAct.setStatusTip(self.tr("Collapse all displayed changes"))
        self.connect(self.collapseAct, qt.SIGNAL("triggered()"), self.slotCollapse)
        #Expand
        self.expandAct = qt.QAction(self.tr("E&xpand"), self)
        self.expandAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'add')))
        self.expandAct.setStatusTip(self.tr("Expand all displayed changes"))
        self.connect(self.expandAct, qt.SIGNAL("triggered()"), self.slotExpand)
        #Help
        self.helpAct = qt.QAction(self.tr("H&elp"), self)
        self.helpAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'help')))
        self.helpAct.setStatusTip(self.tr("A short help"))
        self.connect(self.helpAct, qt.SIGNAL("triggered()"), self.slotHelp)
        #About
        self.aboutAct = qt.QAction(self.tr("A&bout"), self)
        self.aboutAct.setIcon(qt.QIcon(KdelibsUtils.get_iconpath('actions', 'about_kde')))
        self.aboutAct.setStatusTip(self.tr("About this tool"))
        self.connect(self.aboutAct, qt.SIGNAL("triggered()"), self.slotAbout)

    def initMenus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.applyAct)
        self.fileMenu.addAction(self.refreshAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.viewMenu = self.menuBar().addMenu(self.tr("&View"))
        #self.viewMenu.addAction(self.collapseAct)
        #self.viewMenu.addAction(self.expandAct)
        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.helpAct)
        self.helpMenu.addAction(self.aboutAct)

    def initToolBar(self):
        self.fileToolBar = self.addToolBar(self.tr("File"))
        self.fileToolBar.addAction(self.exitAct)
        self.fileToolBar.addAction(self.applyAct)
        self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.refreshAct)
        self.fileToolBar.addSeparator()
        #self.fileToolBar.addAction(self.collapseAct)
        #self.fileToolBar.addAction(self.expandAct)
        #self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.helpAct)
        self.fileToolBar.addAction(self.aboutAct)

    def initWidgets(self):
        self.paned = EtcProposalsPanedView(self, self.proposals, self.controller)
        self.setCentralWidget(self.paned)
        self.paned.show()

    #def initStatusBar():
        # TODO:

    def slotExit (self):
        self.close()

    def slotApply(self):
        self.controller.apply()

    def slotRefresh(self):
        self.controller.refresh()

    def slotCollapse(self):
        # TODO
        pass

    def slotExpand(self):
        # TODO
        pass

    def slotHelp(self):
        # TODO
        pass

    def slotAbout(self):
        # TODO
        pass


class EtcProposalsController(object):
    """EtcProposalsController is the controller in the
    model-view-controller-combination (MVC). It glues the (data-)model
    (EtcProposalsGtkDecorator) and the view (EtcProposalsView). It triggers
    changes in the model while keeping the view in sync. It generates an view
    instance itself when initiated."""
    def __init__(self, proposals):
        self.proposals = proposals
        if len(self.proposals) == 0 and EtcProposalsConfigQt4Decorator().Fastexit():
            raise SystemExit
        self.proposals.warmup_cache()
        self.view = EtcProposalsView(proposals, self)

    def undo_changes(self, changes):
        [change.undo() for change in changes]
        self.proposals.warmup_cache()
        self.view.paned.changesview.update_changes()

    def zap_changes(self, changes):
        [change.zap() for change in changes]
        self.proposals.warmup_cache()
        self.view.paned.changesview.update_changes()

    def use_changes(self, changes):
        [change.use() for change in changes]
        self.proposals.warmup_cache()
        self.view.paned.changesview.update_changes()

    def apply(self):
        self.proposals.apply()
        if len(self.proposals) == 0 and EtcProposalsConfigQt4Decorator().Fastexit():
            # TODO: exit Qt4 main loop
            pass
        self.proposals.warmup_cache()
        self.view.paned.treeview.refresh()
        self.view.paned.changesview.update_changes(lambda: [])

    def refresh(self):
        self.proposals.refresh()
        self.proposals.warmup_cache()
        self.view.paned.treeview.refresh()
        self.view.paned.changesview.update_changes(lambda: [])


def run_frontend():
    if not os.environ.has_key('DISPLAY'):
        raise FrontendFailedException('display environment variable not set')
    a = qt.QApplication([])
    model = EtcProposalsQt4Decorator()
    controller = EtcProposalsController(model)
    a.exec_()

if __name__ == '__main__':
    run_frontend()
