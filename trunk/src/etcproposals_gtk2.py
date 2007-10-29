#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a gtk-frontend to integrate modified configs, post-emerge

__author__ = 'Björn Michaelsen, Christian Glindkamp' 
__version__ = '1.4'
__date__ = '2007-10-25'
__doc__ = """
etcproposals_gtk is a gtk-frontend to integrate modified configs, post-emerge.
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
import os, difflib

try:
    import gtk
except ImportError:
    raise FrontendFailedException('Could not find gtk-bindings.')

class EtcProposalsGtkDecorator(EtcProposals):
    """decoration of EtcProposals"""
    def __init__(self):
        EtcProposals.__init__(self, False)


class EtcProposalsConfigGtkDecorator(EtcProposalsConfig):
    """stub to handle configuration settings for the Gtk GUI"""
    pass

class EtcProposalsMainActiongroup(gtk.ActionGroup):
    def __init__(self, controller):
        gtk.ActionGroup.__init__(self, 'Main')
        self.add_actions([
            ('Filemenu', None, '_File', None, None, None),
            ('Editmenu', None, '_Edit', None, None, None),
            ('Viewmenu', None, '_View', None, None, None),
            ('Helpmenu', None, '_Help', None, None, None),
            ('Quit', gtk.STOCK_QUIT, '_Quit', None, 'Quit without applying changes', gtk.main_quit),
            ('Apply', gtk.STOCK_APPLY, '_Apply', None, 'Apply changes', lambda item: controller.apply()),
            ('Refresh', gtk.STOCK_REFRESH, '_Refresh', None, 'Refresh proposals', lambda item: controller.refresh()),
            ('Collapse', gtk.STOCK_REMOVE, '_Collapse', None, 'Collapse all displayed changes', lambda item: controller.view.on_collapse_all()),
            ('Expand', gtk.STOCK_ADD, '_Expand', None, 'Expand all displayed changes', lambda item: controller.view.on_expand_all()),
            ('Help', gtk.STOCK_HELP, '_Help', None, 'A short help', lambda item: HelpDialog(controller.view)),
            ('About', gtk.STOCK_ABOUT, '_About', None, 'About this tool', lambda item: AboutDialog(controller.view))])


class ScanFSWindow(gtk.Window):
    """ScanFSWindow ."""
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_title('etc-proposals - scanning configuration files')
        self.set_position(gtk.WIN_POS_CENTER)
        self.description_label = gtk.Label()
        self.current_file_label = gtk.Label()
        self.description_label.set_label("Scanning configuration files")
        vbox = gtk.VBox()
        vbox.pack_start(self.description_label, True, False, 1)
        vbox.pack_start(self.current_file_label, True, False, 1)
        self.description_label.show()
        self.add(vbox)
        self.show_all()
    
    def get_current_file(self):
        return self.current_file_label.get_label()

    def set_current_file(self, current_file):
        self.current_file_label.set_label(current_file)

    current_file = property(get_current_file, set_current_file)

class ChangeLabel(gtk.Frame):
    """ChangeLabel is a widget showing all data of an
    EtcProposalsChange but the content. It contains an ChangeStatus,
    an ChangeTitle and an ChangeType."""

    class ChangeType(gtk.VBox):
        """ChangeType is a widget showing if a connected
        EtcProposalChange is Whitespace-Only, a CVS-Header or part of an Unmodified
        file"""
        def __init__(self, change):
            gtk.VBox.__init__(self)
            self.labelstatus = [
                change.is_whitespace_only,
                change.is_cvsheader,
                change.is_unmodified ]
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

    class ChangeTitle(gtk.VBox):
        """ChangeTitle is a widget showing the filename, effected lines
        and proposal number of a connected EtcProposalsChange"""
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

    class ChangeStatus(gtk.HBox):
        """ChangeStatus is a widget showing if a connected
        EtcProposalsChange is selected to be used or zapped. The user can change
        the status of the EtcProposalsChange using the toggle buttons. The
        ChangeStatus uses an EtcProposalsController to change the
        status."""
        def __init__(self, change, controller):
            gtk.HBox.__init__(self)
            self.controller = controller
            self.change = change
            self.updating = False
            self.usebutton = gtk.ToggleButton('Use')
            self.zapbutton = gtk.ToggleButton('Zap')
            self.usebutton.set_size_request(50,50)
            self.zapbutton.set_size_request(50,50)
            self.usebutton.connect('toggled', lambda b: self.on_use_toggled())
            self.zapbutton.connect('toggled', lambda b: self.on_zap_toggled())
            self.pack_start(self.zapbutton, True, False, 2)
            self.pack_start(self.usebutton, True, False, 2)
            self.update_change()
            self.show_all()

        def update_change(self):
            buttonstates = (False, False)
            if self.change.touched:
                if self.change.merge:
                    buttonstates = (True, False)
                else:
                    buttonstates = (False, True)
            self.updating = True;
            self.usebutton.set_active(buttonstates[0])
            self.zapbutton.set_active(buttonstates[1])
            self.updating = False

        def on_zap_toggled(self): 
            if not self.updating:
                if self.zapbutton.get_active():
                    self.controller.zap_changes([self.change])
                else:
                    self.controller.undo_changes([self.change])
    
        def on_use_toggled(self):
            if not self.updating:
                if self.usebutton.get_active():
                    self.controller.use_changes([self.change])
                else:
                    self.controller.undo_changes([self.change])

    def __init__(self, change, controller):
        gtk.Frame.__init__(self)
        self.change = change
        self.title = ChangeLabel.ChangeTitle(change)
        self.type = ChangeLabel.ChangeType(change)
        self.status = ChangeLabel.ChangeStatus(change, controller)
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


class ChangeContent(gtk.VBox):
    """ChangeContent is a widget showing the modified lines of an
    EtcProposalsChange"""
    def __init__(self, change):
        gtk.VBox.__init__(self)
        self.change = change
        self.header = gtk.Label() 
        self.header.set_line_wrap(False)
        self.removetextview = gtk.TextView()
        self.inserttextview = gtk.TextView()
        self.removetextview.modify_base(gtk.STATE_NORMAL, self.removetextview.get_colormap().alloc_color(65000,50000,50000))
        self.inserttextview.modify_base(gtk.STATE_NORMAL, self.inserttextview.get_colormap().alloc_color(50000,65000,50000))
        self.removetextview.modify_text(gtk.STATE_NORMAL, self.removetextview.get_colormap().alloc_color(0,0,0))
        self.inserttextview.modify_text(gtk.STATE_NORMAL, self.inserttextview.get_colormap().alloc_color(0,0,0))
        for textview in [self.removetextview, self.inserttextview]:
            buffer = textview.get_buffer()
            buffer.create_tag('^', underline=True)
            buffer.create_tag('-', underline=True, foreground='DarkRed')
            buffer.create_tag('+', underline=True, foreground='DarkGreen')
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
        headertext = '%s content at lines %d-%d in the file %s' % (
            action,
            affected_lines[0],
            affected_lines[1],
            self.change.get_file_path())
        self.header.set_text(headertext)
        for textview in [self.removetextview, self.inserttextview]:
            if not textview.parent == None:
                self.remove(textview)
        if action in ['delete', 'replace']:
            self.pack_start(self.removetextview, False, False, 2)
        if action in ['insert', 'replace']:
            self.pack_start(self.inserttextview, False, False, 2)
        differ = difflib.Differ()
        insertbuffer=self.inserttextview.get_buffer()
        removebuffer=self.removetextview.get_buffer()
        lastbuffer=None
        for line in differ.compare(self.change.get_base_content(), self.change.get_proposed_content()):
            if line.startswith('+'):
                lastbuffer=insertbuffer
                insertbuffer.insert(insertbuffer.get_end_iter(), line[2:])
            elif line.startswith('-'):
                lastbuffer=removebuffer
                removebuffer.insert(removebuffer.get_end_iter(), line[2:])
            elif line.startswith('?'):
                textiter=lastbuffer.get_end_iter()
                textiter.backward_line()
                for char in line[2:]:
                    if char in '^+-':
                        textenditer=textiter.copy()
                        textenditer.forward_char()
                        lastbuffer.apply_tag_by_name(char, textiter, textenditer)
                    textiter.forward_char()
        for buffer in [insertbuffer, removebuffer]:
            enditer=buffer.get_end_iter()
            enditer.backward_char()
            buffer.delete(enditer, buffer.get_end_iter())

class EtcProposalChangeView(gtk.Expander):
    """EtcProposalChangeView is an widget showing everything about an
    EtcProposalsChange and allows to change its status. It contains an
    ChangeLabel and an ChangeContent. In all, it contains the following objects:
     - ChangeLabel
     - ChangeContent"""
    def __init__(self, change, controller):
        gtk.Expander.__init__(self)
        self.change = change
        label = gtk.Label(self.get_labeltext())
        label.show()
        self.set_label_widget(label)
        box = gtk.VBox()
        box.pack_start(ChangeLabel(change, controller), False, False, 2)
        box.pack_start(ChangeContent(change), False, False, 2)
        box.show_all()
        self.add(box)
        self.show()
    
    def get_labeltext(self):
        affected_lines = self.change.get_affected_lines()
        return '%s:%s-%s(%d)' % (self.change.get_file_path(), affected_lines[0], affected_lines[1], self.change.get_revision())


class EtcProposalsTreeView(gtk.TreeView):
    """EtcProposalsTreeView implements the Treeview for selecting files and changes."""

    class ContextMenu(gtk.Menu):
        """ContextMenu implements the popup menu in the Treeview."""
        def __init__(self):
            gtk.Menu.__init__(self)
            self.useitem = gtk.MenuItem('Use All')
            self.zapitem = gtk.MenuItem('Zap All')
            self.undoitem = gtk.MenuItem('Undo All')
            self.append(self.useitem)
            self.append(self.zapitem)
            self.append(self.undoitem)
            self.show_all()

    def __init__(self, proposals, controller):
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        self.menu = EtcProposalsTreeView.ContextMenu()
        self.column = gtk.TreeViewColumn('')
        self.cell = gtk.CellRendererText()
        self.proposals = proposals
        self.controller = controller
        self.treestore.append(None, ['Filesystem'])
        self.fsrow = self.treestore[0]
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
        self.connect_object('event', self.on_button_press, self.menu)
        self.refresh()
        self.menu.useitem.connect('activate', self.on_use_tv_menu_select) 
        self.menu.zapitem.connect('activate', self.on_zap_tv_menu_select) 
        self.menu.undoitem.connect('activate', self.on_undo_tv_menu_select) 
        self.show()

    def refresh(self):
        [self.treestore.remove(row.iter) for row in self.fsrow.iterchildren()]
        for file in self.proposals.get_files():
            parent=self.fsrow
            for part in file[1:].split('/'):
                rows = [row for row in parent.iterchildren() if row[0]==part]
                if len(rows)==1:
                    parent = rows[0]
                else:
                    parent = self.treestore[self.treestore.append(parent.iter, [part])]
        self.expand_all()

    def get_changegenerator_for_node(self, node):
        """returns a functor that returns a list of EtcProposalChanges belonging to a node."""
        if len(node) == 1 and not (node == (0,)):
            return None
        if node == (1,0):
            return self.proposals.get_whitespace_changes
        elif node == (1,1):
            return self.proposals.get_cvsheader_changes
        elif node == (1,2):
            return self.proposals.get_unmodified_changes
        elif node == (2,0):
            return self.proposals.get_used_changes
        elif node == (2,1):
            return self.proposals.get_zapped_changes
        elif node == (2,2):
            return self.proposals.get_undecided_changes
        elif node == (0,):
            return self.proposals.get_all_changes
        elif node[0] == 0:
            (iter, path) = (self.fsrow.iter, '/')
            for i in node[1:]:
                iter=self.treestore.iter_nth_child(iter, i)
                path=os.path.join(path, self.treestore[iter][0])
            if os.path.isdir(path):
                return lambda: self.proposals.get_dir_changes(path)
            else:
                return lambda: self.proposals.get_file_changes(path)
        return lambda: []
    
    def on_button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            (path, column, x, y) = self.get_path_at_pos(int(event.x), int(event.y))
            self.get_selection().select_path(path)
            widget.popup(None, None, None, event.button, event.time)
            return True
        return False

    def on_use_tv_menu_select(self, widget):
        (model, iter) = self.get_selection().get_selected()
        self.controller.use_changes(self.get_changegenerator_for_node(model.get_path(iter))())

    def on_zap_tv_menu_select(self, widget):
        (model, iter) = self.get_selection().get_selected()
        self.controller.zap_changes(self.get_changegenerator_for_node(model.get_path(iter))())

    def on_undo_tv_menu_select(self, widget):
        (model, iter) = self.get_selection().get_selected()
        self.controller.undo_changes(self.get_changegenerator_for_node(model.get_path(iter))())


class EtcProposalsChangesView(gtk.VBox):
    """EtcProposalsChangesView implements the display a list of changes. It
    uses EtcProposalChangeViews to display the changes. The changes it
    displays are provided by a functor."""
    def __init__(self, controller):
        gtk.VBox.__init__(self)
        self.controller = controller
        self.changes_generator = lambda: []
        self.collapsed_changes = set()
    
    def update_changes(self, changes_generator = None):
        self.hide()
        for child in self.get_children():
            labeltext = child.get_labeltext()
            if not child.get_expanded():
                self.collapsed_changes.add(labeltext)
            elif labeltext in self.collapsed_changes:
                self.collapsed_changes.remove(labeltext)
            self.remove(child)
            while gtk.events_pending():
                gtk.main_iteration()
        if not changes_generator == None:
            self.changes_generator = changes_generator
        for change in self.changes_generator():
            changeview = EtcProposalChangeView(change, self.controller)
            if not changeview.get_labeltext() in self.collapsed_changes:
                changeview.set_expanded(True)
            self.pack_start(changeview, False, False, 0)
            while gtk.events_pending():
                gtk.main_iteration()
        self.show()

    def collapse_all(self):
        [child.set_expanded(False) for child in self.get_children()]
    
    def expand_all(self):
        [child.set_expanded(True) for child in self.get_children()]


class EtcProposalsPanedView(gtk.HPaned):
    """EtcProposalsPanedView is a Panel containing an EtcProposalsTreeView for
    selecting sets of changes and an EtcProposalsChangesView to display
    them."""
    def __init__(self, proposals, controller):
        gtk.HPaned.__init__(self)
        self.controller = controller
        self.proposals = proposals
        self.changesview = EtcProposalsChangesView(self.controller)
        self.treeview = EtcProposalsTreeView(self.proposals, self.controller)
        tv_scrollwindow = gtk.ScrolledWindow()
        cv_scrollwindow = gtk.ScrolledWindow()
        tv_scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        cv_scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        tv_scrollwindow.add_with_viewport(self.treeview)
        cv_scrollwindow.add_with_viewport(self.changesview)
        tv_scrollwindow.set_size_request(200,600)
        self.add1(tv_scrollwindow)
        self.add2(cv_scrollwindow)
        self.treeview.get_selection().set_select_function(self.on_tv_item_selected, None)
        self.show_all()
    
    def on_tv_item_selected(self, selection, user_data):
        changegenerator = self.treeview.get_changegenerator_for_node(selection)
        if changegenerator == None:
            return False
        self.changesview.update_changes(changegenerator)         
        return True


class HelpDialog(gtk.MessageDialog):
    """Shows a short help text"""
    def __init__(self, parent):
        gtk.MessageDialog.__init__(self, parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            """Etc-Proposals is a tool for updating gentoo configuration files
            
You can accept proposals made by a updated package to change your configuration file or reject them. To do the first use the "Use"-Button, otherwise use the "Zap"-Button. If a file has multiple changes, you can make your choice seperately.

You can use or zap all changes in a group in treeview on the right by using the contextmenu that comes up when you click with the right mousebutton there.

Use the "Apply"-Button in the Toolbar to merge the changes to the filesystem.""")
        self.connect("response", lambda *d: self.destroy())
        self.run()
    
        
class AboutDialog(gtk.AboutDialog):
    """AboutDialog just is an About Dialog"""
    def __init__(self, parent):
        gtk.AboutDialog.__init__(self)
        self.set_transient_for(parent)
        self.set_name('Etc-Proposals')
        self.set_version(__version__)
        self.set_copyright('Copyright 2006-2007 Björn Michaelsen')
        self.set_comments('etc-proposals is a tool for merging gentoo configuration files.\netcproposals_lib version:' + __libversion__)
        self.set_website('http://etc-proposals.berlios.de')
        self.set_license('''GNU General Public License, Version 2

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License Version 2 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA''')
        self.set_authors(['Björn Michaelsen', 'Jeremy Wickersheimer', 'Christian Glindkamp'])
        self.show_all()
        self.connect("response", lambda *d: self.destroy())


class EtcProposalsView(gtk.Window):
    """EtcProposalsView is a the Window that displays all the changes. It
    contains a EtcProposalsPanedView and an additional toolbar."""
    def __init__(self, proposals, controller):
        gtk.Window.__init__(self)
        self.controller = controller
        self.set_title('etc-proposals')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('destroy', lambda *w: gtk.main_quit())
        vbox = gtk.VBox()
        self.menubar = self._get_menubar()
        self.menubar.show()
        self.toolbar = self._get_toolbar()
        self.toolbar.show()
        self.paned = EtcProposalsPanedView(proposals, controller)
        vbox.pack_start(self.menubar, False, False, 0)
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(self.paned, True, True, 0)
        vbox.show()
        self.add(vbox)
        self.set_size_request(800,600)
        self.show()

    def on_expand_all(self):
        self.paned.changesview.expand_all()
    
    def on_collapse_all(self):
        self.paned.changesview.collapse_all()

    def _get_menubar(self):
        menu_xml = """
        <ui>
            <menubar name="Menubar">
                <menu action="Filemenu">
                    <menuitem action="Refresh"/>
                    <menuitem action="Apply"/>
                    <menuitem action="Quit"/>
                </menu>
                <menu action="Editmenu">
                </menu>
                <menu action="Viewmenu">
                    <menuitem action="Collapse"/>
                    <menuitem action="Expand"/>
                </menu>
                <menu action="Helpmenu">
                    <menuitem action="Help"/>
                    <menuitem action="About"/>
                </menu>
            </menubar>
        </ui>
        """
        uimanager = gtk.UIManager()
        uimanager.insert_action_group(self.controller.main_actiongroup, 0)
        uimanager.add_ui_from_string(menu_xml)
        menubar = uimanager.get_widget('/Menubar')
        return menubar

    def _get_toolbar(self):
        tb_xml = """
        <ui>
            <toolbar name="Toolbar">
                <toolitem action="Quit"/>
                <toolitem action="Apply"/>
                <separator/>
                <toolitem action="Refresh"/>
                <separator/>
                <toolitem action="Collapse"/>
                <toolitem action="Expand"/>
                <separator/>
                <separator/>
                <toolitem action="Help"/>
                <toolitem action="About"/>
            </toolbar>
        </ui>
        """
        uimanager = gtk.UIManager()
        uimanager.insert_action_group(self.controller.main_actiongroup, 0)
        uimanager.add_ui_from_string(tb_xml)
        toolbar = uimanager.get_widget('/Toolbar')
        #toolitem = gtk.ToolItem()
        #menubar = gtk.MenuBar()
        #typeitem = gtk.MenuItem("Typefilters")
        #typeitem_menu = gtk.Menu()
        #ws_typeitem = gtk.MenuItem("Whitespace")
        #cvs_typeitem = gtk.MenuItem("CVS-Header")
        #unchanged_typeitem = gtk.MenuItem("Unchanged")
        #typeitem_menu.add(gtk.TearoffMenuItem())
        #typeitem_menu.add(ws_typeitem)
        #typeitem_menu.add(cvs_typeitem)
        #typeitem_menu.add(unchanged_typeitem)
        #typeitem.set_submenu(typeitem_menu)
        #menubar.add(typeitem)
        #toolitem.add(menubar)
        #toolitem.set_expand(True)
        #toolitem.add(gtk.Label("Statusfilter:"))
        #toolitem.add(gtk.Label("Statusfilter:"))
        #toolitem.show_all()
        #toolbar.insert(toolitem, 8)
        return toolbar


class EtcProposalsController(object):
    """EtcProposalsController is the controller in the
    model-view-controller-combination (MVC). It glues the (data-)model
    (EtcProposalsGtkDecorator) and the view (EtcProposalsView). It triggers
    changes in the model while keeping the view in sync. It generates an view
    instance itself when initiated."""
    def __init__(self, proposals):
        self.proposals = proposals
        self.main_actiongroup = EtcProposalsMainActiongroup(self)
        if len(self.proposals) == 0 and EtcProposalsConfigGtkDecorator().Fastexit():
            raise SystemExit
        self.view = EtcProposalsView(proposals, self)
        self.refresh()

    def undo_changes(self, changes):
        [change.undo() for change in changes]
        self.view.paned.changesview.update_changes()

    def zap_changes(self, changes):
        [change.zap() for change in changes]
        self.view.paned.changesview.update_changes()

    def use_changes(self, changes):
        [change.use() for change in changes]
        self.view.paned.changesview.update_changes()

    def apply(self):
        self.proposals.apply()
        if len(self.proposals) == 0 and EtcProposalsConfigGtkDecorator().Fastexit():
            gtk.main_quit()
        self.view.paned.treeview.refresh()
        self.view.paned.changesview.update_changes(lambda: [])

    def refresh(self):
        def refresh_callback(current_file):
            wait_win.current_file = current_file
            while gtk.events_pending():
                gtk.main_iteration()
        wait_win = ScanFSWindow()
        self.proposals.refresh(refresh_callback)
        refresh_callback("Refreshing views.")
        self.view.paned.treeview.refresh()
        self.view.paned.changesview.update_changes(lambda: [])
        wait_win.destroy()


def run_frontend():
    if not os.environ.has_key('DISPLAY'):
        raise FrontendFailedException('display environment variable not set')
    model = EtcProposalsGtkDecorator()
    controller =  EtcProposalsController(model)
    gtk.main()


if __name__ == '__main__':
    run_frontend()
