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

The model is represented by the EtcProposals class, whose functionality
is mostly implemented in etcproposals_lib.

The view is implemented by the EtcProposalsView using most of the other helper classes
in this module to show a representation of the model and accept user input.

The controller is implemented by the EtcProposalsController and is used to modify the
model while keeping the view in sync.

Here is a bit of ASCII-art showing the hierachy of objects in the view:
EtcProposalsView (window)
+- (toolbar) -> starts AboutDialog, HelpDialog
+- PanedView
   +- FilesystemTreeView
   +- ChangesView
      +- ChangeView (multiple)
         +- ChangeLabel
         +- ChangeContent
"""
from etcproposals.etcproposals_lib import *
from etcproposals.etcproposals_lib import __version__ as __libversion__
import os, os.path, difflib

try:
    import gtk
except ImportError:
    raise FrontendFailedException('Could not find gtk-bindings.')

#### MVC: Model ####

# see etcproposals_lib

class EtcProposalsConfigGtkDecorator(EtcProposalsConfig):
    """stub to handle configuration settings for the Gtk GUI"""
    pass


#### MVC: View ####
STOCK_PREFIX = 'etcproposals-'
STOCK_CVS = STOCK_PREFIX + 'CVS'
STOCK_WHITESPACE = STOCK_PREFIX + 'WHITESPACE'
STOCK_UNMODIFIED = STOCK_PREFIX + 'UNMODIFIED'

class IconFactory(gtk.IconFactory):
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


class UIManager(gtk.UIManager):
    def __init__(self, view):
        gtk.UIManager.__init__(self)
        xml = """
        <ui>
            <menubar name="Menubar">
                <menu action="Filemenu">
                    <menuitem action="Refresh"/>
                    <menuitem action="Apply"/>
                    <menuitem action="Quit"/>
                </menu>
                <menu action="Editmenu">
            <menuitem action="Use All"/>
            <menuitem action="Zap All"/>
            <menuitem action="Undo All"/>
                </menu>
                <menu action="Viewmenu">
                    <menuitem action="Collapse"/>
                    <menuitem action="Expand"/>
                    <separator/>
                    <menu action="Typefilter">
                        <menu action="Whitespacefilter">
                            <menuitem action="Only Whitespace"/>
                            <menuitem action="Only Non-Whitespace"/>
                            <menuitem action="Whitespacefilter Off"/>
                        </menu>
                        <menu action="CVSHeaderfilter">
                            <menuitem action="Only CVS"/>
                            <menuitem action="Only Non-CVS"/>
                            <menuitem action="CVSHeaderfilter Off"/>
                        </menu>
                        <menu action="Modificationfilter">
                            <menuitem action="Only Unmodified"/>
                            <menuitem action="Only Modified"/>
                            <menuitem action="Modificationfilter Off"/>
                        </menu>
                        <menuitem action="Typefilter Off"/>
                    </menu>
                    <menu action="Statusfilter">
                        <menuitem action="Show Use"/>
                        <menuitem action="Show Zap"/>
                        <menuitem action="Show Undecided"/>
                    </menu>
                </menu>
                <menu action="Helpmenu">
                    <menuitem action="Help"/>
                    <menuitem action="About"/>
                </menu>
            </menubar>
            <toolbar name="Toolbar">
                <toolitem action="Quit"/>
                <toolitem action="Apply"/>
                <separator/>
                <toolitem action="Refresh"/>
                <separator/>
                <toolitem action="Previous Page"/>
                <toolitem action="Next Page"/>
                <separator/>
                <toolitem action="Collapse"/>
                <toolitem action="Expand"/>
                <separator/>
                <toolitem action="Show Use"/>
                <toolitem action="Show Zap"/>
                <toolitem action="Show Undecided"/>
                <separator/>
                <toolitem action="Only CVS"/>
                <toolitem action="Only Unmodified"/>
                <toolitem action="Only Whitespace"/>
                <toolitem action="Typefilter Off"/>
                <placeholder name="Toolbarspace"/>
                <separator/>
                <toolitem action="Help"/>
                <toolitem action="About"/>
            </toolbar>
        <popup name="TreeMenu">
            <menuitem action="Use All"/>
            <menuitem action="Zap All"/>
            <menuitem action="Undo All"/>
        </popup>
        </ui>
        """
        self.insert_action_group(view.main_actiongroup, 0)
        self.add_ui_from_string(xml)
        self.set_add_tearoffs(True)


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
            self.__setup_labels()
            self.update_change()
            self.show()
    
        def __setup_labels(self):
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
            self.usebutton.connect('toggled', lambda b: self.__on_use_toggled())
            self.zapbutton.connect('toggled', lambda b: self.__on_zap_toggled())
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

        def __on_zap_toggled(self): 
            if not self.updating:
                if self.zapbutton.get_active():
                    self.controller.zap_changes([self.change])
                else:
                    self.controller.undo_changes([self.change])
    
        def __on_use_toggled(self):
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
        self.removetextview.modify_base(gtk.STATE_NORMAL, self.removetextview.get_colormap().alloc_color("#FFC4C4"))
        self.inserttextview.modify_base(gtk.STATE_NORMAL, self.inserttextview.get_colormap().alloc_color("#C4FFC4"))
        for textview in [self.removetextview, self.inserttextview]:
            buffer = textview.get_buffer()
            textview.modify_text(gtk.STATE_NORMAL, textview.get_colormap().alloc_color("#000000"))
            buffer.create_tag('^', background="#FFFFC4")
            buffer.create_tag('-', background="#FF4040")
            buffer.create_tag('+', background="#40FF40")
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


class ChangeView(gtk.Expander):
    """ChangeView is an widget showing everything about an
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


class ChangesView(gtk.VBox):
    """ChangesView implements the display a list of changes. It
    uses ChangeViews to display the changes. The changes it
    displays are provided by a functor."""
    def __init__(self, controller, view):
        gtk.VBox.__init__(self)
        self.controller = controller
        self.view = view
        self.changes_generator = lambda: []
        self.changes_list = self.changes_generator()
        self.start_change_index = 0
        self.changes_per_page = 10
        self.collapsed_changes = set()
    
    def update_changes(self, changes_generator = None):
        self.hide()
        self.__remember_collapsed_changes()
        self.__clear_page()
        if not changes_generator == None:
            self.changes_generator = changes_generator
        self.changes_list = self.changes_generator()
        self.start_change_index = 0
        self.__fill_page()
        self.show()

    def show_next_page(self):
        self.hide()
        self.__remember_collapsed_changes()
        self.__clear_page()
        self.start_change_index += self.changes_per_page
        self.__fill_page()
        self.show()

    def has_next_page(self):
        return self.start_change_index + self.changes_per_page < len(self.changes_list)

    def show_previous_page(self):
        self.hide()
        self.__remember_collapsed_changes()
        self.__clear_page()
        self.start_change_index = max(0, self.start_change_index - self.changes_per_page)
        self.__fill_page()
        self.show()

    def has_previous_page(self):
        return self.start_change_index > 0

    def collapse_all(self):
        [child.set_expanded(False) for child in self.get_children()]
    
    def expand_all(self):
        [child.set_expanded(True) for child in self.get_children()]

    def __remember_collapsed_changes(self):
        for child in self.get_children():
            labeltext = child.get_labeltext()
            if not child.get_expanded():
                self.collapsed_changes.add(labeltext)
            elif labeltext in self.collapsed_changes:
                self.collapsed_changes.remove(labeltext)

    def __clear_page(self):
        for child in self.get_children():
            self.remove(child)

    def __fill_page(self):
        last_change_index = self.start_change_index + self.changes_per_page
        last_change_index = min(len(self.changes_list), last_change_index)
        for change in self.changes_list[self.start_change_index:last_change_index]:
            changeview = ChangeView(change, self.controller)
            if not changeview.get_labeltext() in self.collapsed_changes:
                changeview.set_expanded(True)
            self.pack_start(changeview, False, False, 0)


class FilesystemTreeView(gtk.TreeView):
    """FilesystemTreeView implements the Treeview for selecting files and changes."""
    def __init__(self, proposals, controller, view):
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        self.menu = view.uimanager.get_widget('/TreeMenu')
        self.column = gtk.TreeViewColumn('')
        self.cell = gtk.CellRendererText()
        self.proposals = proposals
        self.controller = controller
        self.view = view
        self.treestore.append(None, ['/'])
        self.fsrow = self.treestore[0]
        self.column.pack_start(self.cell, True)
        self.column.add_attribute(self.cell, 'text', 0)
        self.append_column(self.column)
        self.set_headers_visible(False)
        self.connect_object('event', self.on_button_press, self.menu)
        self.refresh()
        self.get_selection().connect('changed', self.view.on_selection_changed)
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
        if node[0] == 0:
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


class PanedView(gtk.HPaned):
    """PanedView is a Panel containing an FilesystemTreeView for
    selecting sets of changes and an ChangesView to display
    them."""
    def __init__(self, proposals, controller, view):
        gtk.HPaned.__init__(self)
        self.controller = controller
        self.proposals = proposals
        self.changesview = ChangesView(self.controller, view)
        self.treeview = FilesystemTreeView(self.proposals, self.controller, view)
        tv_scrollwindow = gtk.ScrolledWindow()
        cv_scrollwindow = gtk.ScrolledWindow()
        tv_scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        cv_scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        tv_scrollwindow.add_with_viewport(self.treeview)
        cv_scrollwindow.add_with_viewport(self.changesview)
        tv_scrollwindow.set_size_request(200,600)
        self.add1(tv_scrollwindow)
        self.add2(cv_scrollwindow)
        self.show_all()
    


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
        self.set_authors(['Björn Michaelsen', 'Jeremy Wickersheimer', 'Christian Glindkamp', 'Jakub Steiner'])
        self.show_all()
        self.connect("response", lambda *d: self.destroy())


class EtcProposalsView(gtk.Window):
    """EtcProposalsView is a the Window that displays all the changes. It
    contains a PanedView and an additional toolbar."""
    def __init__(self, proposals, controller):
        gtk.Window.__init__(self)
        self.controller = controller
        self.ignore_filterchanges = False
        iconfactory = IconFactory()
        iconfactory.add_default()
        self.main_actiongroup = MainActiongroup(self.controller, self)
        self.uimanager = UIManager(self)
        self.set_title('etc-proposals')
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('destroy', lambda *w: gtk.main_quit())
        vbox = gtk.VBox()
        self.menubar = self.__get_menubar()
        self.menubar.show()
        self.toolbar = self.__get_toolbar()
        self.toolbar.show()
        self.paned = PanedView(proposals, controller, self)
        self.selected_node = None
        vbox.pack_start(self.menubar, False, False, 0)
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(self.paned, True, True, 0)
        vbox.show()
        self.add(vbox)
        self.set_size_request(800,600)
        self.selection_path = None
        self.show()

    def update_changes(self, changegenerator = None):
        self.paned.changesview.update_changes(changegenerator)
        self.on_page_changed()

    def on_expand_all(self):
        self.paned.changesview.expand_all()
    
    def on_collapse_all(self):
        self.paned.changesview.collapse_all()

    def on_filter_changed(self):
        if not self.ignore_filterchanges:
            self.update_changes()

    def on_typefilter_off(self):
        self.ignore_filterchanges = True
        self.main_actiongroup.get_action('Modificationfilter Off').set_active(True)
        self.main_actiongroup.get_action('CVSHeaderfilter Off').set_active(True)
        self.main_actiongroup.get_action('Whitespacefilter Off').set_active(True)
        self.ignore_filterchanges = False
        self.on_filter_changed()

    def on_next_page(self):
        self.paned.changesview.show_next_page()
        self.on_page_changed()

    def on_previous_page(self):
        self.paned.changesview.show_previous_page()
        self.on_page_changed()

    def on_page_changed(self):
        previous = self.main_actiongroup.get_action('Previous Page')
        next = self.main_actiongroup.get_action('Next Page')
        previous.set_sensitive(self.paned.changesview.has_previous_page())
        next.set_sensitive(self.paned.changesview.has_next_page())

    def on_selection_changed(self, selection):
        self.update_changes(lambda: self.get_filtered_selection())
        
    def is_not_filtered(self, change):
        if not self.main_actiongroup.show_state(change.get_status()):
            return False
        whitespace_cnd = self.main_actiongroup.get_whitespace_condition()
        if not whitespace_cnd is None:
            if not whitespace_cnd == change.is_whitespace_only():
                return False
        cvs_cnd = self.main_actiongroup.get_cvs_condition()
        if not cvs_cnd is None:
            if not cvs_cnd == change.is_cvsheader():
                return False
        unmodified_cnd = self.main_actiongroup.get_unmodified_condition()
        if not unmodified_cnd is None:
            if not unmodified_cnd == change.is_unmodified():
                return False
        return True

    def get_filtered_selection(self):
        tv = self.paned.treeview
        (model, iter) = tv.get_selection().get_selected()
        return [change for change in
            tv.get_changegenerator_for_node(model.get_path(iter))()
            if self.is_not_filtered(change)]
        
    def __get_menubar(self):
        return self.uimanager.get_widget('/Menubar')

    def __get_toolbar(self):
        toolbar = self.uimanager.get_widget('/Toolbar')
        space_item = gtk.ToolItem()
        space_item.set_expand(True)
        toolbar.insert(space_item, 19)
        toolbar.insert(gtk.SeparatorToolItem(),19)
        toolbar.show_all()
        return toolbar 


class MainActiongroup(gtk.ActionGroup):
    NUMERIC_TO_BOOL = {0: None, 1: True, 2: False}
    STATE_TO_ACTION = { 'use' : 'Show Use', 'zap' : 'Show Zap', 'undecided' : 'Show Undecided'}
    
    def __init__(self, controller, view):
        gtk.ActionGroup.__init__(self, 'Main')
        self.add_actions([
            ('Filemenu', None, '_File', None, None, None),
            ('Editmenu', None, '_Edit', None, None, None),
            ('Viewmenu', None, '_View', None, None, None),
            ('Helpmenu', None, '_Help', None, None, None),
            ('Quit', gtk.STOCK_QUIT, '_Quit', None, 'Quit without applying changes', gtk.main_quit),
            ('Apply', gtk.STOCK_APPLY, '_Apply', None, 'Apply changes', lambda item: controller.apply()),
            ('Refresh', gtk.STOCK_REFRESH, '_Refresh', None, 'Refresh proposals', lambda item: controller.refresh()),
            ('Collapse', gtk.STOCK_REMOVE, '_Collapse Changes', None, 'Collapse all displayed changes', lambda item: view.on_collapse_all()),
            ('Expand', gtk.STOCK_ADD, '_Expand Changes', None, 'Expand all displayed changes', lambda item: view.on_expand_all()),
            ('Use All', gtk.STOCK_OK, 'Use All Undecided', None, 'use all filtered changes in the current selection', lambda item: controller.on_use_selection()),
            ('Zap All', gtk.STOCK_CANCEL, 'Zap All Undecided', None, 'zap all filtered changes in the current selection', lambda item: controller.on_zap_selection()),
            ('Undo All', gtk.STOCK_UNDO, 'Undo All', None, 'undo all filtered changes in the current selection', lambda item: controller.on_undo_selection()),
            ('Help', gtk.STOCK_HELP, '_Help', None, 'A short help', lambda item: HelpDialog(view)),
            ('About', gtk.STOCK_ABOUT, '_About', None, 'About this tool', lambda item: AboutDialog(view)),
            ('Previous Page', gtk.STOCK_GO_BACK, 'Previous Page', None, 'show the next page of changes', lambda item: view.on_previous_page()),
            ('Next Page', gtk.STOCK_GO_FORWARD, 'Next Page', None, 'show the previous page of changes', lambda item:view.on_next_page()),
            ('Typefilter', None, 'Type Filter', None, None, None),
            ('Statusfilter', None, 'Status Filter', None, None, None),
            ('Whitespacefilter', STOCK_WHITESPACE, 'Whitespace Filter', None, None, None),
            ('CVSHeaderfilter', STOCK_CVS, 'CVS-Header Filter', None, None, None),
            ('Modificationfilter', STOCK_UNMODIFIED, 'Modification Filter', None, None, None),
            ('Typefilter Off', gtk.STOCK_CLEAR, 'No Type Filtering', None, 'Disable all type filters', lambda item: view.on_typefilter_off())
            ])
        self.add_toggle_actions([
            ('Show Use', gtk.STOCK_OK, 'Show Used Changes', None, 'Show used changes', lambda item: view.on_filter_changed(), True),
            ('Show Zap', gtk.STOCK_CANCEL, 'Show Zapped Changes', None, 'Show zapped changes', lambda item: view.on_filter_changed(), True),
            ('Show Undecided', gtk.STOCK_DIALOG_QUESTION, 'Show Undecided Changes', None, 'Show undecided changes', lambda item: view.on_filter_changed(), True)
            ])
        self.add_radio_actions([
            ('Only Whitespace', STOCK_WHITESPACE, 'Only Whitespace Changes', None, 'Show only whitespace changes', 1),
            ('Only Non-Whitespace', None, 'Only Non-Whitespace Changes', None, 'Show only non-whitespace changes', 2),
            ('Whitespacefilter Off', None, 'No Whitespace Filtering', None, 'Disable whitespace filtering', 0)],
            on_change = lambda item, current: view.on_filter_changed())
        self.add_radio_actions([
            ('Only CVS', STOCK_CVS, 'Only CVS-Header Changes', None, 'Show only CVS-header changes', 1),
            ('Only Non-CVS', None, 'Only Non-CVS-Header Changes', None, 'Show only non-CVS-header changes', 2),
            ('CVSHeaderfilter Off', None, 'No CVS-Header Filtering', None, 'Disable CVS-header filtering', 0)],
            on_change = lambda item, current: view.on_filter_changed())
        self.add_radio_actions([
            ('Only Unmodified', STOCK_UNMODIFIED, 'Only Unmodified Changes', None, 'Show only unmodified changes', 1),
            ('Only Modified', None, 'Only Modified Changes', None, 'Show only modified changes', 2),
            ('Modificationfilter Off', None, 'No Modification Filtering', None, 'Disable modification filtering', 0)],
            on_change = lambda item, current: view.on_filter_changed())

    def get_whitespace_condition(self):
        return MainActiongroup.NUMERIC_TO_BOOL[self.get_action('Only Whitespace').get_current_value()]

    def get_cvs_condition(self):
        return MainActiongroup.NUMERIC_TO_BOOL[self.get_action('Only CVS').get_current_value()]
        
    def get_unmodified_condition(self):
        return MainActiongroup.NUMERIC_TO_BOOL[self.get_action('Only Unmodified').get_current_value()]

    def show_state(self, state):
        return self.get_action(MainActiongroup.STATE_TO_ACTION[state]).get_active()


#### MVC: Controller ####
class EtcProposalsController(object):
    """EtcProposalsController is the controller in the
    model-view-controller-combination (MVC). It glues the (data-)model
    (EtcProposals) and the view (EtcProposalsView). It triggers
    changes in the model while keeping the view in sync. It generates an view
    instance itself when initiated."""
    def __init__(self, proposals):
        self.proposals = proposals
        if len(self.proposals) == 0 and EtcProposalsConfigGtkDecorator().Fastexit():
            raise SystemExit
        self.view = EtcProposalsView(proposals, self)
        self.refresh()

    def undo_changes(self, changes):
        [change.undo() for change in changes]
        self.view.update_changes()

    def zap_changes(self, changes):
        [change.zap() for change in changes]
        self.view.update_changes()

    def use_changes(self, changes):
        [change.use() for change in changes]
        self.view.update_changes()

    def apply(self):
        self.proposals.apply()
        if len(self.proposals) == 0 and EtcProposalsConfigGtkDecorator().Fastexit():
            gtk.main_quit()
        self.view.paned.treeview.refresh()
        self.view.on_selection(None)
        self.view.update_changes()

    def refresh(self):
        def refresh_callback(current_file):
            wait_win.current_file = current_file
            while gtk.events_pending():
                gtk.main_iteration()
        wait_win = ScanFSWindow()
        self.proposals.refresh(refresh_callback)
        refresh_callback("Refreshing views.")
        self.view.paned.treeview.refresh()
        self.view.update_changes()
        wait_win.destroy()

    def on_undo_selection(self):
        changes = self.__get_filtered_decided_selection()
        while len(changes):
            [change.undo() for change in changes]
            changes = self.__get_filtered_decided_selection()
        self.view.update_changes()

    def on_zap_selection(self):
        changes = self.__get_filtered_undecided_selection()
        while len(changes):
            [change.zap() for change in changes]
            changes = self.__get_filtered_undecided_selection()
        self.view.update_changes()

    def on_use_selection(self):
        changes = self.__get_filtered_undecided_selection()
        while len(changes):
            [change.use() for change in changes]
            changes = self.__get_filtered_undecided_selection()
        self.view.update_changes()
    
    def __get_filtered_undecided_selection(self):
        return [change for change in 
            self.view.get_filtered_selection()
            if change.get_status() == 'undecided']

    def __get_filtered_decided_selection(self):
        return [change for change in 
            self.view.get_filtered_selection()
            if not change.get_status() == 'undecided']


def run_frontend():
    if not os.environ.has_key('DISPLAY'):
        raise FrontendFailedException('display environment variable not set')
    model = EtcProposals()
    controller =  EtcProposalsController(model)
    gtk.main()


if __name__ == '__main__':
    run_frontend()
