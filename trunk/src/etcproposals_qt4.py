#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Wickersheimer Jeremy
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a gtk-frontend to integrate modified configs, post-emerge

__author__ = 'Wickersheimer Jeremy'
__version__ = '1.0'
__date__ = '2007-03-18'

from etcproposals.etcproposals_lib import *
from etcproposals.etcproposals_lib import __version__ as __libversion__
import os

try:
    import PyQt4.Qt as qt
except ImportError:
    raise FrontendFailedException('Could not find qt4-bindings.')

class EtcProposalsQt4Decorator(EtcProposals):
    def warmup_cache(self):
        """for the GUI,  we need to keep the cache warm"""
        self.get_whitespace_changes()
        self.get_cvsheader_changes()
        self.get_unmodified_changes()
        self.get_used_changes()
        self.get_zapped_changes()
        self.get_undecided_changes()


class EtcProposalsController(object):
    def __init__(self, proposals):
        self.proposals = proposals
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
        self.proposals.warmup_cache()
        self.view.paned.treeview.refresh()
        self.view.paned.changesview.update_changes(lambda: [])


class EtcProposalsTreeView(qt.QFrame):
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
	#print "(get_changegenerator_for_node) nodes: " + str(nodes)
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
	    #print "parent: " + str(nodes[0].parent())
	    if nodes[0].parent() == self.fsnode:
	        file = nodes[0].text(0)
                return lambda: self.proposals.get_file_changes(file)
	    else:
                return lambda: []

    #def on_button_press(self, widget, event):
        #if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            #(path, column, x, y) = self.get_path_at_pos(int(event.x), int(event.y))
            #self.get_selection().select_path(path)
            #widget.popup(None, None, None, event.button, event.time)
            #return True
        #return False


class EtcProposalChangeType(qt.QFrame):
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


class EtcProposalChangeTitle(qt.QFrame):
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


class EtcProposalChangeStatus(qt.QFrame):
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

    def button_toggled(self, clicked):
	#print "Button " + str(clicked) + " was clicked"
	if not self.updating:
	    if self.usebutton.isChecked():
		if clicked != self.usebutton:
		    self.usebutton.setChecked(False)
		else:
	            #print "USE"
		    self.zapbutton.setChecked(False)
		    self.controller.use_changes([self.change])
	    elif self.zapbutton.isChecked():
	        #print "ZAP"
		self.usebutton.setChecked(False)
		self.controller.zap_changes([self.change])
	    else:
	        #print "No state"
		self.controller.undo_changes([self.change])

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


class EtcProposalChangeLabel(qt.QFrame):
    def __init__(self, parent, change, controller):
        qt.QFrame.__init__(self, parent)
	self.setFrameStyle(qt.QFrame.StyledPanel | qt.QFrame.Raised)
        self.change = change
        self.title = EtcProposalChangeTitle(self, change)
        self.type = EtcProposalChangeType(self, change)
        self.status = EtcProposalChangeStatus(self, change, controller)
	self.layout = qt.QHBoxLayout(self)
        self.layout.addWidget(self.status)
	self.layout.addWidget(self.title)
	self.layout.addWidget(self.type)
        self.show()

    def update_change(self):
        for control in [self.title, self.type]:
            control.update_change()


class EtcProposalChangeContent(qt.QFrame):
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
            #textview.show()
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
    def __init__(self, parent, change, controller):
        qt.QFrame.__init__(self, parent)
	self.layout = qt.QVBoxLayout(self)
        self.change = change
        self.label = qt.QLabel(self.get_labeltext(), self)
        self.layout.addWidget(self.label)
	self.layout.addWidget(EtcProposalChangeLabel(self, change, controller))
	self.layout.addWidget(EtcProposalChangeContent(self, change))

    def get_labeltext(self):
        affected_lines = self.change.get_affected_lines()
        return '%s:%s-%s(%d)' % (self.change.get_file_path(), affected_lines[0], affected_lines[1], self.change.get_revision())


class EtcProposalsChangesView(qt.QFrame):
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
	    #print "(update_changes) Remove item :" + str(i)
	    i.hide()
            self.layout.removeWidget(i)
	if not changes_generator == None:
            self.changes_generator = changes_generator
        for change in self.changes_generator():
            changeview = EtcProposalsChangeView(self, change, self.controller)
	    #print "(update_changes) Add item :" + str(changeview)
	    self.changeList.append(changeview)
	    self.layout.addWidget(changeview)
	    changeview.show()
	#print "(update_changes) Now has :" + str(len(self.changeList)) + " items."
	self.show()

    #def collapse_all(self):
        #[child.set_expanded(False) for child in self.get_children()]

    #def expand_all(self):
        #[child.set_expanded(True) for child in self.get_children()]


class EtcProposalsPanedView(qt.QSplitter):
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
	#print "[SIGNAL] Selected item changed in treeview"
        changegenerator = self.treeview.get_changegenerator_for_node(self.treeview.treeview.selectedItems())
        if changegenerator == None:
            return False
        self.changesview.update_changes(changegenerator)
        return True

    def on_use_tv_menu_select(self, widget):
	return
        #(model, iter) = self.treeview.get_selection().get_selected()
        #self.controller.use_changes(self.treeview.get_changegenerator_for_node(model.get_path(iter))())

    def on_zap_tv_menu_select(self, widget):
	return
        #(model, iter) = self.treeview.get_selection().get_selected()
        #self.controller.zap_changes(self.treeview.get_changegenerator_for_node(model.get_path(iter))())

    def on_undo_tv_menu_select(self, widget):
	return
        #(model, iter) = self.treeview.get_selection().get_selected()
        #self.controller.undo_changes(self.treeview.get_changegenerator_for_node(model.get_path(iter))())


class EtcProposalsView(qt.QMainWindow):
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
	self.exitAct.setIcon(qt.QIcon("/usr/kde/3.5/share/icons/crystalsvg/22x22/actions/exit.png"))
	self.exitAct.setShortcut(self.tr("Ctrl+Q"))
	self.exitAct.setStatusTip(self.tr("Exit the application"))
	self.connect(self.exitAct, qt.SIGNAL("triggered()"), self.slotExit)
	#Apply
	self.applyAct = qt.QAction(self.tr("A&pply"), self)
	self.applyAct.setIcon(qt.QIcon("/usr/kde/3.5/share/icons/crystalsvg/22x22/actions/button_ok.png"))
	self.applyAct.setStatusTip(self.tr("Apply selected changes"))
	self.connect(self.applyAct, qt.SIGNAL("triggered()"), self.slotApply)

    def initMenus(self):
	self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
	self.fileMenu.addAction(self.applyAct)
	self.fileMenu.addSeparator()
	self.fileMenu.addAction(self.exitAct)

    def initToolBar(self):
	self.fileToolBar = self.addToolBar(self.tr("File"))
	self.fileToolBar.addAction(self.exitAct)
	self.fileToolBar.addAction(self.applyAct)

    def initWidgets(self):
	self.paned = EtcProposalsPanedView(self, self.proposals, self.controller)
	self.setCentralWidget(self.paned)
	self.paned.show()

    #def initStatusBar():
	#todo

    def slotExit (self):
	self.close()

    def slotApply(self):
	self.controller.apply()

def run_frontend():
    if not os.environ.has_key('DISPLAY'):
        raise FrontendFailedException('display environment variable not set')
    a = qt.QApplication([])
    model = EtcProposalsQt4Decorator()
    controller = EtcProposalsController(model)
    a.exec_()

if __name__ == '__main__':
    run_frontend()