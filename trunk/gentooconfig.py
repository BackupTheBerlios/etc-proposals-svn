#!/usr/bin/env python

import getopt
import gtk
import sys

def bak(obj):
	print 'Toolbar Button pressed!'
	print obj

class MergeToolbar(gtk.Toolbar):
	def __init__(self):
		gtk.Toolbar.__init__(self)
		self.set_style(gtk.TOOLBAR_ICONS)
		self.set_tooltips(True)

		self.append_widget(gtk.Label('Change'),'These buttons affect a single change', 'Change')
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GOTO_TOP, gtk.ICON_SIZE_MENU)
		self.append_item('Start', 'Go to start of file', 'Start', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_MENU)
		self.append_item('Previous change', 'Go up to previous change', 'Previous', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_MENU)
		self.append_item('Next change', 'Go down to next change', 'Next', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GOTO_BOTTOM, gtk.ICON_SIZE_MENU)
		self.append_item('End', 'Go to end of file', 'End', image, bak)

		self.append_space()
		self.append_widget(gtk.Label('Changeset'),'These buttons affect the changeset', 'Changeset')

		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_MENU)
		self.append_item('Undo', 'Undo', 'Undo all changes and go back to last change', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_MENU)
		self.append_item('Restart', 'Restart editing this change', 'Restart', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU)
		self.append_item('Edit All', 'Enable editing of unchnaged parts of file', 'Edit', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU)
		self.append_item('Apply', 'Apply this and go to next change', 'Apply', image, bak)

		self.append_space()
		self.append_widget(gtk.Label('Configuration file'),'These buttons affect configuration file', 'Changeset')

		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
		self.append_item('Cancel', 'Undo all changes and quit', 'Cancel', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_MENU)
		self.append_item('Quit', 'Quit editing this file', 'Quit', image, bak)

class MergeWindow:
	def __init__(self):
		self.window = gtk.Window()
		vbox = gtk.VBox()
		self.title = gtk.Label('/etc/make.conf')
		self.toolbar = MergeToolbar()
		self.textview = gtk.TextView()
		self.statusbar = gtk.Statusbar()
		vbox.pack_start(self.title, False, False);
		vbox.pack_start(self.toolbar, False, False);
		vbox.pack_start(self.textview);
		vbox.pack_start(self.statusbar, False, False);
		self.window.add(vbox)
		context = self.statusbar.get_context_id('statusbar')
		self.statusbar.push(context, 'Merging file /etc/._cfg000_make.conf')
		self.window.show_all()


window = MergeWindow()
gtk.main()

# vim:ts=4 sw=4 noet:
