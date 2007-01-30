#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a gtk-frontend to integrate modified configs, post-emerge

__author__ = 'Björn Michaelsen' 
__version__ = '1.0'
__date__ = '2007-01-25'

import gtk

class EtcProposalChangeStatusRow(gtk.HBox):
    def __init__(self, change):
        gtk.HBox.__init__(self)
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
        [self.pack_start(label, True, False, 10) for label in self.labels]

    def update_change(self):
        for (label, status, text) in zip(self.labels, self.labelstatus, self.labeltexts()):
            if status():
                label.set_label(text)
            else:
                label.set_label('')
    
    @staticmethod
    def labeltexts():
        return ['whitespace', 'cvs-header', 'unchanged']


