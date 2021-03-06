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
import os, os.path, difflib, sys

try:
    import gtk, gobject
except ImportError:
    raise FrontendFailedException('Could not find gtk-bindings.')

#### MVC: Model ####

# see etcproposals_lib

class EtcProposalsGtk2Config(object):
    """stub to handle configuration settings for the Gtk GUI"""
    def __init__(self):
        try:
            self.__max_changes_per_page = Config.parser.getint('Gtk2', 'MaxChangesPerPage')
        except Exception:
            self.__max_changes_per_page = 10
    	
    MaxChangesPerPage = property(lambda self: self.__max_changes_per_page)


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
    def __init__(self):
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
        self.add_ui_from_string(xml)
        self.props.add_tearoffs = True


class WaitWindow(gtk.Window):
    """WaitWindow ."""
    def __init__(self):
        gtk.Window.__init__(self)
        self.props.title = 'etc-proposals - please wait'
        self.set_position(gtk.WIN_POS_CENTER)
        self.description_label = gtk.Label()
        self.current_file_label = gtk.Label()
        self.description_label.props.label = "Scanning configuration files"
        vbox = gtk.VBox()
        vbox.pack_start(self.description_label, True, False, 1)
        vbox.pack_start(self.current_file_label, True, False, 1)
        self.description_label.show()
        self.add(vbox)
        self.show_all()
    
    def set_description(self, description):
        self.description_label.props.label = description

    def set_current_file(self, current_file):
        self.current_file_label.props.label = current_file

    def refreshing_views(self):
        self.description = 'Refreshing Views.'
        self.current_file = ''

    current_file = property(fset = set_current_file)
    description = property(fset = set_description)


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
                    label.props.label = text
                else:
                    label.props.label = ''
        
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
            self.filenamelabel.props.label = self.change.get_file_path()
            self.proposallabel.props.label = 'Proposal: %s' % self.change.get_revision()
            self.lineslabel.props.label = 'Lines: %d-%d' % self.change.get_affected_lines()

    class ChangeStatus(gtk.HBox):
        """ChangeStatus is a widget showing if a connected
        EtcProposalsChange is selected to be used or zapped. The user can change
        the status of the EtcProposalsChange using the toggle buttons. The
        ChangeStatus uses an EtcProposalsController to change the
        status."""
        __gsignals__ = {
            'use-change' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
            'zap-change' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
            'undo-change' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()) }
        def __init__(self, change):
            gtk.HBox.__init__(self)
            self.change = change
            self.updating = False
            self.usebutton = gtk.ToggleButton('Use')
            self.zapbutton = gtk.ToggleButton('Zap')
            self.usebutton.set_size_request(50, 50)
            self.zapbutton.set_size_request(50, 50)
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
            self.usebutton.props.active = buttonstates[0]
            self.zapbutton.props.active = buttonstates[1]
            self.updating = False

        def __on_zap_toggled(self): 
            if not self.updating:
                if self.zapbutton.props.active:
                    self.emit('zap-change')
                else:
                    self.emit('undo-change')
    
        def __on_use_toggled(self):
            if not self.updating:
                if self.usebutton.props.active:
                    self.emit('use-change')
                else:
                    self.emit('undo-change')

    def __init__(self, change):
        gtk.Frame.__init__(self)
        self.change = change
        self.title = ChangeLabel.ChangeTitle(change)
        self.type = ChangeLabel.ChangeType(change)
        self.status = ChangeLabel.ChangeStatus(change)
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
            buffer = textview.props.buffer
            textview.modify_text(gtk.STATE_NORMAL, textview.get_colormap().alloc_color("#000000"))
            buffer.create_tag('^', background="#FFFFC4")
            buffer.create_tag('-', background="#FF4040")
            buffer.create_tag('+', background="#40FF40")
            textview.props.editable = False
            textview.props.cursor_visible = False
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
        insertbuffer=self.inserttextview.props.buffer
        removebuffer=self.removetextview.props.buffer
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
    def __init__(self, change):
        gtk.Expander.__init__(self)
        self.change = change
        minilabel = gtk.Label(self.get_labeltext())
        self.props.label_widget = minilabel
        biglabel = ChangeLabel(change)
        self.status = biglabel.status
        box = gtk.VBox()
        box.pack_start(biglabel, False, False, 2)
        box.pack_start(ChangeContent(change), False, False, 2)
        self.add(box)
        self.show_all()
    
    def get_labeltext(self):
        affected_lines = self.change.get_affected_lines()
        return '%s:%s-%s(%d)' % (self.change.get_file_path(), affected_lines[0], affected_lines[1], self.change.get_revision())


class ChangesView(gtk.VBox):
    """ChangesView implements the display a list of changes. It
    uses ChangeViews to display the changes. The changes it
    displays are provided by a functor."""
    __gsignals__ = { 'new-changeview' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)) }
    class ChangesCache(list):
        def __init__(self, change_generator):
            self.change_generator = change_generator

        def assure_changes_up_to(self, max):
            for idx in range(max-len(self)+1):
                try:
                    self.append(self.change_generator.next())
                except StopIteration:
                    break
 
    def __init__(self):
        gtk.VBox.__init__(self)
        self.changes_list = []
        self.start_change_index = 0
        self.changes_per_page = Gtk2Config.MaxChangesPerPage
        self.collapsed_changes = set()
    
    def update_changes(self, changes_generator):
        self.hide()
        self.start_change_index = 0
        self.changes_list = ChangesView.ChangesCache(changes_generator)
        self.__refill()

    def show_next_page(self):
        self.start_change_index += self.changes_per_page
        self.__refill()

    def has_next_page(self):
        return self.start_change_index + self.changes_per_page < len(self.changes_list)

    def show_previous_page(self):
        self.start_change_index = max(0, self.start_change_index - self.changes_per_page)
        self.__refill()

    def has_previous_page(self):
        return self.start_change_index > 0

    def collapse_all(self):
        for child in self.get_children():
            child.props.expanded = False
    
    def expand_all(self):
        for child in self.get_children():
            child.props.expanded = True

    def __last_change_index(self):
        last_change_index = self.start_change_index + self.changes_per_page
        return min(len(self.changes_list), last_change_index)

    def __refill(self):
        self.hide()
        self.__remember_collapsed_changes()
        self.__clear_page()
        self.__fill_page()
        self.show()

    def __remember_collapsed_changes(self):
        for child in self.get_children():
            labeltext = child.get_labeltext()
            if not child.props.expanded:
                self.collapsed_changes.add(labeltext)
            elif labeltext in self.collapsed_changes:
                self.collapsed_changes.remove(labeltext)

    def __clear_page(self):
        for child in self.get_children():
            self.remove(child)

    def __fill_page(self):
        self.changes_list.assure_changes_up_to(self.start_change_index + self.changes_per_page + 1)
        last_change_index = self.__last_change_index()
        for change in self.changes_list[self.start_change_index:last_change_index]:
            changeview = ChangeView(change)
            if not changeview.get_labeltext() in self.collapsed_changes:
                changeview.props.expanded = True
            self.pack_start(changeview, False, False, 0)
	    self.emit('new-changeview', changeview)


class FilesystemTreeView(gtk.TreeView):
    """FilesystemTreeView implements the Treeview for selecting files and changes."""
    def __init__(self, proposals):
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        self.column = gtk.TreeViewColumn('')
        self.cell = gtk.CellRendererText()
        self.proposals = proposals
        self.treestore.append(None, ['/'])
        self.fsrow = self.treestore[0]
        self.column.pack_start(self.cell, True)
        self.column.add_attribute(self.cell, 'text', 0)
        self.append_column(self.column)
        self.props.headers_visible = False
        self.refresh()
        self.show()

    def on_button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            (path, column, x, y) = self.get_path_at_pos(int(event.x), int(event.y))
            self.get_selection().select_path(path)
            widget.popup(None, None, None, event.button, event.time)
            return True
        return False

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
                return self.proposals.get_dir_changes_gen(path)
            else:
                return self.proposals.get_file_changes_gen(path)
        return (change for change in [])
    


class PanedView(gtk.HPaned):
    """PanedView is a Panel containing an FilesystemTreeView for
    selecting sets of changes and an ChangesView to display
    them."""
    def __init__(self, proposals):
        gtk.HPaned.__init__(self)
        self.changesview = ChangesView()
        self.treeview = FilesystemTreeView(proposals)
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
        self.props.transient_for = parent
        self.props.name = 'Etc-Proposals'
        self.props.version = __version__
        self.props.copyright = 'Copyright 2006-2007 Björn Michaelsen'
        self.props.comments = 'etc-proposals is a tool for merging gentoo configuration files.\netcproposals_lib version:' + __libversion__
        self.props.website = 'http://etc-proposals.berlios.de'
        self.props.license = '''GNU General Public License, Version 2

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
        self.props.authors = ['Björn Michaelsen (Backend, Readline, Gtk2)', 'Jeremy Wickersheimer (Qt4)', 'Christian Glindkamp (Gtk2)']
        self.props.artists = ['Björn Michaelsen', 'Jakub Steiner', 'Andreas Nilsson']
        self.show_all()
        self.connect("response", lambda *d: self.destroy())


class EtcProposalsView(gtk.Window):
    """EtcProposalsView is a the Window that displays all the changes. It
    contains a PanedView and an additional toolbar."""
    def __init__(self, proposals):
        gtk.Window.__init__(self)
        iconfactory = IconFactory()
        iconfactory.add_default()
        self.ignore_filterchanges = False
        self.main_actiongroup = MainActiongroup()
        self.uimanager = UIManager()
        self.uimanager.insert_action_group(self.main_actiongroup, 0)
        self.main_actiongroup.attach_accelgroup_to_window(self)
        self.props.title = 'etc-proposals'
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('destroy', lambda *w: gtk.main_quit())
        vbox = gtk.VBox()
        self.menubar = self.uimanager.get_widget('/Menubar')
        self.menubar.show()
        self.toolbar = self.__get_toolbar()
        self.toolbar.show()
        self.popupmenu = self.uimanager.get_widget('/TreeMenu')
        paned = PanedView(proposals)
        self.selected_node = None
        vbox.pack_start(self.menubar, False, False, 0)
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(paned, True, True, 0)
        vbox.show()
        self.add(vbox)
        self.set_size_request(800,600)
        self.selection_path = None
        self.treeview = paned.treeview
        self.changesview = paned.changesview
        self.__register_events()
        self.show()
        
    def __register_events(self):
        self.treeview.get_selection().connect('changed', self.on_selection_changed)
        simple_actions = {
            'Quit': lambda item: gtk.main_quit(),
            'Collapse': lambda item: self.on_collapse_all(),
            'Expand': lambda item: self.on_expand_all(),
            'Help': lambda item: self.on_show_help(),
            'About': lambda item: self.on_show_about(),
            'Previous Page': lambda item: self.on_previous_page(),
            'Next Page': lambda item: self.on_next_page(),
            'Typefilter Off': lambda item: self.on_typefilter_off() }
        toggle_actions = {
            'Show Use': lambda item: self.on_filter_changed(),
            'Show Zap': lambda item: self.on_filter_changed(),
            'Show Undecided': lambda item: self.on_filter_changed() }
        radio_actions = {
            'Whitespacefilter Off': lambda item, current: self.on_filter_changed(),
            'CVSHeaderfilter Off': lambda item, current: self.on_filter_changed(),
            'Modificationfilter Off': lambda item, current: self.on_filter_changed() }
        for (action, callback) in simple_actions.items():
            self.main_actiongroup.get_action(action).connect('activate', callback)
        for (action, callback) in toggle_actions.items():
            self.main_actiongroup.get_action(action).connect('toggled', callback)
        for (action, callback) in radio_actions.items():
            self.main_actiongroup.get_action(action).connect('changed', callback)

    def on_expand_all(self):
        self.changesview.expand_all()
    
    def on_collapse_all(self):
        self.changesview.collapse_all()

    def on_next_page(self):
        self.changesview.show_next_page()
        self.on_page_changed()

    def on_previous_page(self):
        self.changesview.show_previous_page()
        self.on_page_changed()
    
    def on_filter_changed(self):
        if not self.ignore_filterchanges:
            self.update_changes()

    def on_typefilter_off(self):
        self.ignore_filterchanges = True
        for actionname in ['Modificationfilter Off', 'CVSHeaderfilter Off', 'Whitespacefilter Off']:
            self.main_actiongroup.get_action(actionname).props.active = True
        self.ignore_filterchanges = False
        self.on_filter_changed()

    def on_page_changed(self):
        previous = self.main_actiongroup.get_action('Previous Page')
        next = self.main_actiongroup.get_action('Next Page')
        previous.props.sensitive = self.changesview.has_previous_page()
        next.props.sensitive = self.changesview.has_next_page()

    def on_selection_changed(self, selection):
        self.update_changes()
        
    def on_show_about(self):
        AboutDialog(self)

    def on_show_help(self):
        HelpDialog(self)

    def update_changes(self, changegenerator = None):
        if changegenerator is None:
            changegenerator = self.get_filtered_selection()
        self.changesview.update_changes(changegenerator)
        self.on_page_changed()

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
        (model, iter) = self.treeview.get_selection().get_selected()
        if iter is None:
            return (change for change in [])
        return (change for change in
            self.treeview.get_changegenerator_for_node(model.get_path(iter))
            if self.is_not_filtered(change))

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
    
    def __init__(self):
        gtk.ActionGroup.__init__(self, 'Main')
        self.accel_group = gtk.AccelGroup()
        self.add_actions([
            ('Filemenu', None, '_File', None, None),
            ('Editmenu', None, '_Edit', None, None),
            ('Viewmenu', None, '_View', None, None),
            ('Helpmenu', None, '_Help', None, None),
            ('Quit', gtk.STOCK_QUIT, 'Quit', '<Alt>F4', 'Quit without applying changes'),
            ('Apply', gtk.STOCK_APPLY, 'Apply', None, 'Apply changes'),
            ('Refresh', gtk.STOCK_REFRESH, 'Refresh', 'F5', 'Refresh proposals'),
            ('Collapse', gtk.STOCK_REMOVE, 'Collapse Changes', None, 'Collapse all displayed changes'),
            ('Expand', gtk.STOCK_ADD, 'Expand Changes', None, 'Expand all displayed changes'),
            ('Use All', gtk.STOCK_OK, 'Use All Undecided', '<Control>u', 'use all filtered changes in the current selection'),
            ('Zap All', gtk.STOCK_CANCEL, 'Zap All Undecided', '<Control><Shift>z', 'zap all filtered changes in the current selection'),
            ('Undo All', gtk.STOCK_UNDO, 'Undo All', '<Control>z', 'undo all filtered changes in the current selection'),
            ('Help', gtk.STOCK_HELP, 'Help', 'F1', 'A short help'),
            ('About', gtk.STOCK_ABOUT, 'About', None, 'About this tool'),
            ('Previous Page', gtk.STOCK_GO_BACK, 'Previous Page', None, 'show the next page of changes'),
            ('Next Page', gtk.STOCK_GO_FORWARD, 'Next Page', None, 'show the previous page of changes'),
            ('Typefilter', None, 'Type Filter', None, None),
            ('Statusfilter', None, 'Status Filter', None, None),
            ('Whitespacefilter', STOCK_WHITESPACE, 'Whitespace Filter', None, None),
            ('CVSHeaderfilter', STOCK_CVS, 'CVS-Header Filter', None, None),
            ('Modificationfilter', STOCK_UNMODIFIED, 'Modification Filter', None, None),
            ('Typefilter Off', gtk.STOCK_CLEAR, 'No Type Filtering', None, 'Disable all type filters')
            ])
        self.add_toggle_actions([
            ('Show Use', gtk.STOCK_OK, 'Show Used Changes', None, 'Show used changes', None, True),
            ('Show Zap', gtk.STOCK_CANCEL, 'Show Zapped Changes', None, 'Show zapped changes', None, True),
            ('Show Undecided', gtk.STOCK_DIALOG_QUESTION, 'Show Undecided Changes', None, 'Show undecided changes', None, True)
            ])
        self.add_radio_actions([
            ('Only Whitespace', STOCK_WHITESPACE, 'Only Whitespace Changes', None, 'Show only whitespace changes', 1),
            ('Only Non-Whitespace', None, 'Only Non-Whitespace Changes', None, 'Show only non-whitespace changes', 2),
            ('Whitespacefilter Off', None, 'No Whitespace Filtering', None, 'Disable whitespace filtering', 0)])
        self.add_radio_actions([
            ('Only CVS', STOCK_CVS, 'Only CVS-Header Changes', None, 'Show only CVS-header changes', 1),
            ('Only Non-CVS', None, 'Only Non-CVS-Header Changes', None, 'Show only non-CVS-header changes', 2),
            ('CVSHeaderfilter Off', None, 'No CVS-Header Filtering', None, 'Disable CVS-header filtering', 0)])
        self.add_radio_actions([
            ('Only Unmodified', STOCK_UNMODIFIED, 'Only Unmodified Changes', None, 'Show only unmodified changes', 1),
            ('Only Modified', None, 'Only Modified Changes', None, 'Show only modified changes', 2),
            ('Modificationfilter Off', None, 'No Modification Filtering', None, 'Disable modification filtering', 0)])
        for action in self.list_actions():
            action.set_accel_group(self.accel_group)

    def attach_accelgroup_to_window(self, window):
        window.add_accel_group(self.accel_group)
        for action in self.list_actions():
            action.connect_accelerator()

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
        if len(self.proposals) == 0 and Config.Fastexit:
            raise SystemExit
        self.view = EtcProposalsView(proposals)
        self.main_actiongroup = self.view.main_actiongroup
        self.changesview = self.view.changesview
        self.treeview = self.view.treeview
        self.popupmenu = self.view.popupmenu
        self.__register_events()
        self.refresh()

    def __register_events(self):
        self.treeview.connect_object('event', self.treeview.on_button_press, self.popupmenu)
        self.changesview.connect('new-changeview', self.on_new_changeview)
        simple_actions = {
            'Apply': lambda item: self.apply(),
            'Refresh': lambda item: self.refresh(),
            'Use All': lambda item: self.on_use_selection(),
            'Zap All': lambda item: self.on_zap_selection(),
            'Undo All': lambda item: self.on_undo_selection() }
        for (action, callback) in simple_actions.items():
            self.main_actiongroup.get_action(action).connect('activate', callback)

    def undo_change(self, change):
        change.undo()
        self.view.update_changes()

    def zap_change(self, change):
        change.zap()
        self.view.update_changes()

    def use_change(self, change):
        change.use()
        self.view.update_changes()

    def apply(self):
        def apply_callback(current_file):
            wait_win.current_file = current_file
            while gtk.events_pending():
                gtk.main_iteration()
        wait_win = WaitWindow()
        wait_win.description = 'Applying changes'
        self.proposals.apply(current_file_callback=apply_callback)
        if len(self.proposals) == 0 and Config.Fastexit:
            gtk.main_quit()
        wait_win.refreshing_views()
        self.treeview.refresh()
        self.view.update_changes()
        wait_win.destroy()

    def refresh(self):
        def refresh_callback(current_file):
            wait_win.current_file = current_file
            while gtk.events_pending():
                gtk.main_iteration()
        wait_win = WaitWindow()
        self.proposals.refresh(refresh_callback)
        wait_win.refreshing_views()
        self.treeview.refresh()
        self.view.update_changes()
        wait_win.destroy()

    def on_undo_selection(self):
        wait_win = WaitWindow()
        wait_win.description = 'Undoing choices for changes'
        self.__process_all_changes(
            wait_win,
            self.__get_filtered_decided_selection,
            lambda change: change.undo());
        wait_win.refreshing_views()
        self.view.update_changes()
        wait_win.destroy()

    def on_zap_selection(self):
        wait_win = WaitWindow()
        wait_win.description = 'Marking Changes for Zapping'
        changes = list(self.__get_filtered_undecided_selection())
        self.__process_all_changes(
            wait_win,
            self.__get_filtered_undecided_selection,
            lambda change: change.zap());
        wait_win.refreshing_views()
        self.view.update_changes()
        wait_win.destroy()

    def on_use_selection(self):
        wait_win = WaitWindow()
        wait_win.description = 'Marking Changes for Using'
        self.__process_all_changes(
            wait_win,
            self.__get_filtered_undecided_selection,
            lambda change: change.use());
        wait_win.refreshing_views()
        self.view.update_changes()
        wait_win.destroy()

    def on_new_changeview(self, changesview, changeview):
        changeview.status.connect('use-change', lambda changeview: self.use_change(changeview.change))
        changeview.status.connect('zap-change', lambda changeview: self.zap_change(changeview.change))
        changeview.status.connect('undo-change', lambda changeview: self.undo_change(changeview.change))

    def __get_filtered_undecided_selection(self):
        return (change for change in 
            self.view.get_filtered_selection()
            if change.get_status() == 'undecided')

    def __get_filtered_decided_selection(self):
        return (change for change in 
            self.view.get_filtered_selection()
            if not change.get_status() == 'undecided')

    def __process_all_changes(self, wait_win, changessource, operation):
        changes = list(changessource())
        while len(changes):
            for change in changes:
                wait_win.current_file = change.get_file_path()
                operation(change)
                while gtk.events_pending():
                    gtk.main_iteration()
            changes = list(changessource())


# Singletons

Gtk2Config = EtcProposalsGtk2Config()

def run_frontend():
    if not os.environ.has_key('DISPLAY'):
        raise FrontendFailedException('display environment variable not set')
    model = EtcProposals()
    controller =  EtcProposalsController(model)
    gtk.main()


if __name__ == '__main__':
    run_frontend()
