#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Wickersheimer Jeremy, Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a qt4-frontend to integrate modified configs, post-emerge

__author__ = 'Jeremy Wickersheimer, Björn Michaelsen, Christian Glindkamp'
__version__ = '1.3'
__date__ = '2007-06-06'
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
from etcproposals.etcproposals_tools import get_command_output_iterator
import os

try:
    import PyQt4.Qt as qt
except ImportError:
    raise FrontendFailedException('Could not find qt4-bindings.')


    ICON_PATH = '/usr/share/etcproposals'
    ICON_EXT = '.svg'
    def __init__(self):
        gtk.IconFactory.__init__(self)
        for icon_id in [STOCK_CVS, STOCK_WHITESPACE, STOCK_UNMODIFIED]:
            source = gtk.IconSource()
            source.set_filename(os.path.join(IconFactory.ICON_PATH, icon_id.lower() + IconFactory.ICON_EXT))
            iconset = gtk.IconSet()
            iconset.add_source(source)
            self.add(icon_id, iconset)
class IconUtils(object):
    ICONDIR_PATH = '/usr/share/etcproposals'
    IMAGEFORMATS = ['svg', 'png']

    @staticmethod
    def get_iconpath(iconname):
        for format in IconUtils.IMAGEFORMATS:
            path = os.path.join(IconUtils.ICONDIR_PATH, 'qt4_' + iconname + '.' + format)
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
            self.filenamelabel.setAlignment(qt.Qt.AlignHCenter)
            self.proposallabel.setAlignment(qt.Qt.AlignHCenter)
            self.lineslabel.setAlignment(qt.Qt.AlignHCenter)
            self.proposallinesbox = qt.QFrame(self)
            self.proposallinesboxlayout = qt.QHBoxLayout(self.proposallinesbox)
            self.layout.addWidget(self.filenamelabel)
            self.layout.addWidget(self.proposallinesbox)
            self.proposallinesboxlayout.addWidget(self.proposallabel, 1)
            self.proposallinesboxlayout.addWidget(self.lineslabel, 1)
            self.proposallinesboxlayout.setMargin(0)
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
        self.removetextview = qt.QLabel(self)
        self.inserttextview = qt.QLabel(self)
        self.removetextview.palette().setColor(qt.QPalette.Window, qt.QColor(255, 200, 200))
        self.inserttextview.palette().setColor(qt.QPalette.Window, qt.QColor(200, 255, 200))
        self.removetextview.palette().setColor(qt.QPalette.WindowText, qt.QColor(0, 0, 0))
        self.inserttextview.palette().setColor(qt.QPalette.WindowText, qt.QColor(0, 0, 0))
        self.removetextview.setAutoFillBackground(True)
        self.inserttextview.setAutoFillBackground(True)
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.removetextview)
        self.layout.addWidget(self.inserttextview)
        self.layout.setMargin(0)
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
        self.removetextview.setText(''.join(self.change.get_base_content())[:-1])
        self.inserttextview.setText(''.join(self.change.get_proposed_content())[:-1])


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
        self.layout.setMargin(0)

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
        self.treeview.setHeaderLabel("Proposals")
        self.treeview.header().hide()
        # add top item
        self.fsnode = qt.QTreeWidgetItem(self.treeview, ["Filesystem"])
        # add top item
        self.typenode = qt.QTreeWidgetItem(self.treeview, ["Type"])
        self.type_whitespace = qt.QTreeWidgetItem(self.typenode, ["Whitespace"])
        self.type_cvs = qt.QTreeWidgetItem(self.typenode, ["CVS-Header"])
        self.type_unmodified = qt.QTreeWidgetItem(self.typenode, ["Unmodified"])
        self.typenode.setExpanded(True)
        # add top item
        self.statusnode = qt.QTreeWidgetItem(self.treeview, ["Status"])
        self.status_use = qt.QTreeWidgetItem(self.statusnode, ["Use"])
        self.status_zap = qt.QTreeWidgetItem(self.statusnode, ["Zap"])
        self.status_undecided = qt.QTreeWidgetItem(self.statusnode, ["Undecided"])
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
        self.fsnode.takeChildren()
        for file in self.proposals.get_files():
            parent = self.fsnode
            for part in file[1:].split('/'):
                items = [parent.child(i) for i in xrange(0, parent.childCount()) if parent.child(i).text(0) == part]
                if len(items) == 1:
                    parent = items[0]
                else:
                    parent = qt.QTreeWidgetItem(parent, [part])
        self.treeview.expandAll()

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
        elif nodes[0] == self.typenode or nodes[0] == self.statusnode:
            return lambda: []
        else:
            (child,path) = (nodes[0], [])
            while child != self.fsnode:
                path.insert(0, str(child.text(0)))
                child = child.parent()
            path = reduce(lambda x,y: os.path.join(x,y), path, '/')
            if os.path.isdir(path):
                return lambda: self.proposals.get_dir_changes(path)
            else:
                return lambda: self.proposals.get_file_changes(path)


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
        self.setSizePolicy(qt.QSizePolicy.Preferred, qt.QSizePolicy.Maximum)
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
        self.treeview.menu.addAction("Use All", self.on_use_tv_menu_select)
        self.treeview.menu.addAction("Zap All", self.on_zap_tv_menu_select)
        self.treeview.menu.addAction("Undo All", self.on_undo_tv_menu_select)
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


class AboutDialog(qt.QMessageBox):
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
        self.exitAct = qt.QAction("E&xit", self)
        self.exitAct.setIcon(qt.QIcon(IconUtils.get_iconpath('exit')))
        self.exitAct.setShortcut("Ctrl+Q")
        self.exitAct.setStatusTip("Exit the application")
        self.connect(self.exitAct, qt.SIGNAL("triggered()"), self.slotExit)
        #Apply
        self.applyAct = qt.QAction("A&pply", self)
        self.applyAct.setIcon(qt.QIcon(IconUtils.get_iconpath('ok')))
        self.applyAct.setStatusTip("Apply selected changes")
        self.connect(self.applyAct, qt.SIGNAL("triggered()"), self.slotApply)
        #Refresh
        self.refreshAct = qt.QAction("R&efresh", self)
        self.refreshAct.setIcon(qt.QIcon(IconUtils.get_iconpath('reload')))
        self.refreshAct.setStatusTip("Refresh proposals")
        self.connect(self.refreshAct, qt.SIGNAL("triggered()"), self.slotRefresh)
        #Collapse
        self.collapseAct = qt.QAction("C&ollapse", self)
        self.collapseAct.setIcon(qt.QIcon(IconUtils.get_iconpath('add')))
        self.collapseAct.setStatusTip("Collapse all displayed changes")
        self.connect(self.collapseAct, qt.SIGNAL("triggered()"), self.slotCollapse)
        #Expand
        self.expandAct = qt.QAction("E&xpand", self)
        self.expandAct.setIcon(qt.QIcon(IconUtils.get_iconpath('add')))
        self.expandAct.setStatusTip("Expand all displayed changes")
        self.connect(self.expandAct, qt.SIGNAL("triggered()"), self.slotExpand)
        #Help
        self.helpAct = qt.QAction("H&elp", self)
        self.helpAct.setIcon(qt.QIcon(IconUtils.get_iconpath('help')))
        self.helpAct.setStatusTip("A short help")
        self.connect(self.helpAct, qt.SIGNAL("triggered()"), self.slotHelp)
        #About
        self.aboutAct = qt.QAction("A&bout", self)
        self.aboutAct.setIcon(qt.QIcon(IconUtils.get_iconpath('about')))
        self.aboutAct.setStatusTip("About this tool")
        self.connect(self.aboutAct, qt.SIGNAL("triggered()"), self.slotAbout)

    def initMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.applyAct)
        self.fileMenu.addAction(self.refreshAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.viewMenu = self.menuBar().addMenu("&View")
        #self.viewMenu.addAction(self.collapseAct)
        #self.viewMenu.addAction(self.expandAct)
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.helpAct)
        self.helpMenu.addAction(self.aboutAct)

    def initToolBar(self):
        self.fileToolBar = self.addToolBar("File")
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
        # FIXME: Use HelpDialog when its done
        text = """Etc-Proposals is a tool for updating gentoo configuration files
            
You can accept proposals made by a updated package to change your configuration file or reject them. To do the first use the "Use"-Button, otherwise use the "Zap"-Button. If a file has multiple changes, you can make your choice seperately.

You can use or zap all changes in a group in treeview on the right by using the contextmenu that comes up when you click with the right mousebutton there.

Use the "Apply"-Button in the Toolbar to merge the changes to the filesystem."""
        qt.QMessageBox.information(None, 'etc-proposals help', text, qt.QMessageBox.Ok) 

    def slotAbout(self):
        # FIXME: use AboutDialog when its done
        text = 'etc-proposals is a tool for merging gentoo configuration files.\netcproposals_lib version: ' + __libversion__ + '\n'
        text = text + 'Copyright 2006-2007 Björn Michaelsen\n'
        text = text + 'http://etc-proposals.berlios.de\n\n'
        text = text + '''GNU General Public License, Version 2

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License Version 2 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA'''
        text = text + '\n\nAuthors: ' + __author__
        qt.QMessageBox.information(None, 'About etc-proposals', text, qt.QMessageBox.Ok) 

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
            # TODO: clean exit of Qt4 main loop
            raise SystemExit
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
