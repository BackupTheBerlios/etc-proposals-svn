#!/usr/bin/python -O

import getopt
import gtk
import sys

def bak(obj):
	print 'Toolbar Button pressed!'
	print obj

class Filepart:
	def __init__(self, textview, position, text):
		self.textview = textview

		buffer = self.textview.get_buffer()
		self.tag = buffer.create_tag(None)
		self.start_mark = buffer.create_mark(None, position, True)
		anchor = buffer.create_child_anchor(position)
		buffer.insert(position, '\n')

		self.start_text_mark = buffer.create_mark(None, position, True)
		buffer.insert(position, text)
		self.end_mark = buffer.create_mark(None, position, False)

		# HACK Widgettag shouldnt be anonymous
		widgettag = buffer.create_tag(None, editable = False)
		buffer.apply_tag(widgettag, self.start_iter(), self.start_text_iter())
		buffer.apply_tag(self.tag, self.start_text_iter(), self.end_iter())

		self._setup_widgets(anchor)
		self._setup_tag_properties()

	def _setup_widgets(self, anchor):
		self.textview.add_child_at_anchor(gtk.Label('Unchanged part'), anchor)
	
	def _setup_tag_properties(self):
		pass
	
	def start_iter(self):
		return self.textview.get_buffer().get_iter_at_mark(self.start_mark)

	def start_text_iter(self):
		return self.textview.get_buffer().get_iter_at_mark(self.start_text_mark)

	def end_iter(self):
		return self.textview.get_buffer().get_iter_at_mark(self.end_mark)


class CommonFilepart(Filepart):
	def _setup_widgets(self, anchor):
		self.textview.add_child_at_anchor(gtk.Button('Hide this part'), anchor)
	
	def _setup_tag_properties(self):
		self.tag.set_property('editable', False)


class OldFilepart(Filepart):
	def _setup_widgets(self, anchor):
		self.textview.add_child_at_anchor(gtk.Button('Remove this part'), anchor)
	
	def _setup_tag_properties(self):
		self.tag.set_property('editable', True)
		self.tag.set_property('foreground', 'green')

class NewFilepart(Filepart):
	def _setup_widgets(self, anchor):
		self.textview.add_child_at_anchor(gtk.Button('Include this part'), anchor)
	
	def _setup_tag_properties(self):
		self.tag.set_property('editable', True)
		self.tag.set_property('foreground', 'red')
		self.tag.set_property('strikethrough', True)

class MergeToolbar(gtk.Toolbar):
	def __init__(self):
		gtk.Toolbar.__init__(self)
		self.set_style(gtk.TOOLBAR_ICONS)
		self.set_tooltips(True)

		self.append_widget(gtk.Label('Change'),'These buttons affect a single change', 'Change')
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GOTO_TOP, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Start', 'Go to start of file', 'Start', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Previous change', 'Go up to previous change', 'Previous', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Next change', 'Go down to next change', 'Next', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_GOTO_BOTTOM, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('End', 'Go to end of file', 'End', image, bak)

		self.append_space()
		self.append_widget(gtk.Label('Changeset'),'These buttons affect the changeset', 'Changeset')

		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Undo', 'Undo', 'Undo all changes and go back to last change', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Restart', 'Restart editing this change', 'Restart', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Edit All', 'Enable editing of unchnaged parts of file', 'Edit', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Apply', 'Apply this and go to next change', 'Apply', image, bak)

		self.append_space()
		self.append_widget(gtk.Label('Configuration file'),'These buttons affect configuration file', 'Changeset')

		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.append_item('Cancel', 'Undo all changes and quit', 'Cancel', image, bak)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_LARGE_TOOLBAR)
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
		#self.textview.set_editable(False)
		Filepart(self.textview, self.textview.get_buffer().get_end_iter(), 'USE="-*"\n\n')
		OldFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'ACCEPTED_KEYWORDS="~x86"\n# No risk, no fun!\n')
		NewFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'ACCEPTED_KEYWORDS="x86"\n# Play it safe.\n')
		self.window.show_all()


window = MergeWindow()
gtk.main()

# vim:ts=4 sw=4 noet:
