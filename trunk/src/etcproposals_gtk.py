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


class EtcProposalChangeGtkDecorator(EtcProposalChange):
    pass


class EtcProposalGtkDecorator(EtcProposal):
    # Being picky, we only want decorated Changes
    def _create_change(self, opcode):
        return EtcProposalChangeShellDecorator(opcode, self)


class EtcProposalsGtkDecorator(EtcProposals):
    # Being picky, we only want decorated Proposals
    def _create_proposal(self, proposal_path):
        return EtcProposalGtkDecorator(proposal_path, self)


class EtcProposalsConfigGtkDecorator(EtcProposalsConfig):
    pass


class EtcProposalChangeTypeGtk(gtk.VBox):
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


class EtcProposalChangeTitleGtk(gtk.VBox):
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


class EtcProposalChangeStatusGtk(gtk.VBox):
    def __init__(self, change):
        gtk.VBox.__init__(self)
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
            self.change.zap()
            self.usebutton.set_active(False)
        else:
            self.change.undo()

    def on_use_toggled(self):
        if self.usebutton.get_active():
            self.change.use()
            self.zapbutton.set_active(False)
        else:
            self.change.undo()


class EtcProposalChangeLabelGtk(gtk.Frame):
    def __init__(self, change):
        gtk.Frame.__init__(self)
        self.change = change
        self.title = EtcProposalChangeTitleGtk(change)
        self.type = EtcProposalChangeTypeGtk(change)
        self.status = EtcProposalChangeStatusGtk(change)
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


class EtcProposalChangeContentGtk(gtk.VBox):
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


class EtcProposalChangeDecoratorGtk(gtk.Expander):
    def __init__(self, change):
        gtk.Expander.__init__(self)
        self.change = change
        affected_lines = self.change.get_affected_lines()
        label = gtk.Label('%s:%s-%s(%d)' % (self.change.get_file_path(), affected_lines[0], affected_lines[1], self.change.get_revision()))
        label.show()
        self.set_label_widget(label)
        box = gtk.VBox()
        box.pack_start(EtcProposalChangeLabelGtk(change), False, False, 2)
        box.pack_start(EtcProposalChangeContentGtk(change), False, False, 2)
        box.show()
        self.add(box)
        self.show()
