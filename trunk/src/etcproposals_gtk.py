#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a gtk-frontend to integrate modified configs, post-emerge

__author__ = 'Björn Michaelsen' 
__version__ = '1.0'
__date__ = '2007-01-25'

from etcproposals.etcproposals_lib import *
import gtk


class EtcProposalsConfigGtkDecorator(EtcProposalsConfig):
    pass


class EtcProposalChangeType(gtk.VBox):
    def __init__(self, change):
        gtk.VBox.__init__(self)
        self.labelstatus = [
            change.is_whitespace_only,
            change.is_cvsheader,
            change.is_unchanged ]
        self.setup_labels()
        self.update_change()
        self.show()

    def setup_labels(self):
        self.labels = map(lambda x: gtk.Label(), xrange(3)) 
        [label.show() for label in self.labels]
        [self.pack_start(label, True, False, 1) for label in self.labels]

    def update_change(self):
        for (label, status, text) in zip(self.labels, self.labelstatus, self.labeltexts()):
            if status():
                label.set_label(text)
            else:
                label.set_label('')
    
    @staticmethod
    def labeltexts():
        return ['whitespace', 'cvs-header', 'unchanged']


class EtcProposalChangeTitle(gtk.VBox):
    def __init__(self, change):
        gtk.VBox.__init__(self)
        self.change = change
        self.filenamelabel = gtk.Label()
        self.proposallabel = gtk.Label()
        self.lineslabel = gtk.Label()
        proposallinesbox = gtk.HBox()
        self.pack_start(self.filenamelabel, True, False, 2)
        self.pack_start(proposallinesbox, True, False, 2)
        proposallinesbox.pack_start(self.proposallabel, True, False, 2)
        proposallinesbox.pack_start(self.lineslabel, True, False, 2)
        self.update_change()
        for control in [self.filenamelabel, self.proposallabel, self.lineslabel, proposallinesbox, self]:
            control.show()

    def update_change(self):
        self.filenamelabel.set_label(self.change.get_file_path())
        self.proposallabel.set_label('Proposal: %s' % self.change.get_revision())
        self.lineslabel.set_label('Lines: %d-%d' % self.change.get_affected_lines())


class EtcProposalChangeStatus(gtk.VBox):
    def __init__(self, change, controller):
        gtk.VBox.__init__(self)
        self.controller = controller
        self.change = change
        self.usebutton = gtk.ToggleButton('Use')
        self.zapbutton = gtk.ToggleButton('Zap')
        self.usebutton.connect('toggled', lambda b: self.on_use_toggled())
        self.zapbutton.connect('toggled', lambda b: self.on_zap_toggled())
        self.pack_start(self.usebutton, True, False, 2)
        self.pack_start(self.zapbutton, True, False, 2)
        self.update_change()
        for control in [self.usebutton, self.zapbutton, self]:
            control.show()

    def update_change(self):
        buttonstates = (False, False)
        if self.change.touched:
            if self.change.merge:
                buttonstates = (True, False)
            else:
                buttonstates = (False, True)
        self.usebutton.set_active(buttonstates[0])
        self.zapbutton.set_active(buttonstates[1])
    
    def on_zap_toggled(self):
        if self.zapbutton.get_active():
            self.controller.zap_changes([self.change])
        else:
            self.controller.undo_changes([self.change])

    def on_use_toggled(self):
        if self.usebutton.get_active():
            self.controller.use_changes([self.change])
        else:
            self.controller.undo_changes([self.change])


class EtcProposalChangeLabel(gtk.Frame):
    def __init__(self, change, controller):
        gtk.Frame.__init__(self)
        self.change = change
        self.title = EtcProposalChangeTitle(change)
        self.type = EtcProposalChangeType(change)
        self.status = EtcProposalChangeStatus(change, controller)
        box = gtk.HBox()
        box.pack_start(self.status, False, False, 10)
        box.pack_start(self.title, True, True, 10)
        box.pack_start(self.type, False, False, 10)
        box.show()
        self.add(box)
        self.show()
    
    def update_change(self):
        for control in [self.title, self.type]:
            control.update_change()


class EtcProposalChangeContent(gtk.VBox):
    def __init__(self, change):
        gtk.VBox.__init__(self)
        self.change = change
        self.header = gtk.Label() 
        self.header.set_line_wrap(False)
        self.removetextview = gtk.TextView()
        self.inserttextview = gtk.TextView()
        self.removetextview.modify_base(gtk.STATE_NORMAL, self.removetextview.get_colormap().alloc_color(65000,50000,50000))
        self.inserttextview.modify_base(gtk.STATE_NORMAL, self.inserttextview.get_colormap().alloc_color(50000,65000,50000))
        for textview in [self.removetextview, self.inserttextview]:
            buffer = textview.get_buffer()
            textview.set_editable(False)
            textview.set_cursor_visible(False)
            textview.show()
        self.header.show()
        self.pack_start(self.header, False, False, 2)
        self.update_change()
        self.show()
    
    def update_change(self):
        action = self.change.get_action()
        affected_lines = self.change.get_affected_lines()
        headertext = 'This change proposes to %s content at lines %d-%d in the file %s' % (
            action,
            affected_lines[0],
            affected_lines[1],
            self.change.get_file_path())
        self.header.set_text(headertext)
        for textview in [self.removetextview, self.inserttextview]:
            if not textview.parent == None:
                self.remove(textview)
        if action in ['remove', 'replace']:
            self.pack_start(self.removetextview, False, False, 2)
        if action in ['insert', 'replace']:
            self.pack_start(self.inserttextview, False, False, 2)
        self.removetextview.get_buffer().set_text(self.change.get_base_content())
        self.inserttextview.get_buffer().set_text(self.change.get_proposed_content())


class EtcProposalsChangeView(gtk.Expander):
    def __init__(self, change, controller):
        gtk.Expander.__init__(self)
        self.change = change
        affected_lines = self.change.get_affected_lines()
        label = gtk.Label('%s:%s-%s(%d)' % (self.change.get_file_path(), affected_lines[0], affected_lines[1], self.change.get_revision()))
        label.show()
        self.set_label_widget(label)
        box = gtk.VBox()
        box.pack_start(EtcProposalChangeLabel(change, controller), False, False, 2)
        box.pack_start(EtcProposalChangeContent(change), False, False, 2)
        box.show_all()
        self.add(box)
        self.show()


class EtcProposalsTreeViewMenu(gtk.Menu):
    def __init__(self):
        gtk.Menu.__init__(self)
        self.append(gtk.MenuItem('Use All'))
        self.append(gtk.MenuItem('Zap All'))
        self.append(gtk.MenuItem('Undo All'))
        self.show_all()

    
class EtcProposalsTreeView(gtk.TreeView):
    def __init__(self, proposals):
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        self.menu = EtcProposalsTreeViewMenu()
        self.column = gtk.TreeViewColumn('')
        self.cell = gtk.CellRendererText()
        self.proposals = proposals
        self.fsnode = self.treestore.append(None, ['Filesystem'])
        typenode = self.treestore.append(None, ['Type'])
        self.treestore.append(typenode, ['Whitespace'])
        self.treestore.append(typenode, ['CVS-Header'])
        self.treestore.append(typenode, ['Unmodified'])
        statusnode = self.treestore.append(None, ['Status'])
        self.treestore.append(statusnode, ['Use'])
        self.treestore.append(statusnode, ['Zap'])
        self.treestore.append(statusnode, ['Undecided'])
        self.column.pack_start(self.cell, True)
        self.column.add_attribute(self.cell, 'text',0)
        self.append_column(self.column)
        self.set_headers_visible(False)
        self.connect_object('event', self.button_press, self.menu)
        self.refresh()
        self.show()
    
    def refresh(self):
        files = self.proposals.get_files()
        filenode = self.treestore.iter_children(self.fsnode)
        while( filenode != None ):
            self.treestore.remove(filenode)
            filenode = self.treestore.iter_children(self.fsnode)
        for file in self.proposals.get_files():
            self.treestore.append(self.fsnode, [file])
    
    def button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            (path, column, x, y) = self.get_path_at_pos(int(event.x), int(event.y))
            self.get_selection().select_path(path)
            widget.popup(None, None, None, event.button, event.time)
            return True
        return False


class EtcProposalsChangesView(gtk.ScrolledWindow):
    def __init__(self, controller):
        gtk.ScrolledWindow.__init__(self)
        self.controller = controller
        self.changes_generator = lambda: []
        self.vbox = gtk.VBox()
        self.vbox.show()
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.add_with_viewport(self.vbox)
        self.set_size_request(600, 500)
        self.show_all()
    
    def update_changes(self, changes_generator = None):
        for child in self.vbox.get_children():
            self.vbox.remove(child)
        if not changes_generator == None:
            self.changes_generator = changes_generator
        for change in self.changes_generator():
            self.vbox.pack_start(EtcProposalsChangeView(change, self.controller), False, False, 0)


class EtcProposalsPanedView(gtk.HPaned):
    def __init__(self, proposals, controller):
        gtk.HPaned.__init__(self)
        self.proposals = proposals
        self.changesview = EtcProposalsChangesView(controller)
        self.treeview = EtcProposalsTreeView(self.proposals)
        self.add1(self.changesview)
        self.rightbox = gtk.VBox()
        self.rightbox.pack_start(self.treeview, True, True, 0)
        self.rightbox.pack_end(gtk.Button('Apply'), False, False, 0)
        self.rightbox.show_all()
        self.add2(self.rightbox)
        self.treeview.get_selection().set_select_function(self.on_tv_item_selcted, None)
        self.show()
    
    def on_tv_item_selcted(self, selection, user_data):
        if len(selection) == 1 and not (selection == (0,)):
            return False
        if selection == (1,0):
            self.changesview.update_changes(lambda: self.proposals.get_whitespace_changes())
        elif selection == (1,1):
            self.changesview.update_changes(lambda: self.proposals.get_cvsheader_changes())
        elif selection == (1,2):
            self.changesview.update_changes(lambda: self.proposals.get_unmodified_changes())
        elif selection == (2,0):
            self.changesview.update_changes(lambda: [change for change in self.proposals.get_all_changes() if change.get_status() == 'use'])
        elif selection == (2,1):
            self.changesview.update_changes(lambda: [change for change in self.proposals.get_all_changes() if change.get_status() == 'zap'])
        elif selection == (2,2):
            self.changesview.update_changes(lambda: [change for change in self.proposals.get_all_changes() if change.get_status() == 'undecided'])
        return True


class EtcProposalsView(gtk.Window):
    def __init__(self, proposals, controller):
        gtk.Window.__init__(self)
        self.paned = EtcProposalsPanedView(proposals, controller)
        self.add(self.paned)
        self.set_size_request(800,600)
        self.show()


class EtcProposalsController(object):
    def __init__(self, proposals):
        self.proposals = proposals
        self.view = EtcProposalsView(proposals, self)
        
    def undo_changes(self, changes):
        [change.undo() for change in changes]
        self.view.paned.changesview.update_changes()

    def zap_changes(self, changes):
        [change.zap() for change in changes]
        self.view.paned.changesview.update_changes()

    def use_changes(self, changes):
        [change.use() for change in changes]
        self.view.paned.changesview.update_changes()
