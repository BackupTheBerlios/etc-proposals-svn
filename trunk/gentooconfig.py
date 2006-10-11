#!/usr/bin/python -O

import getopt
import gtk
import pango
import sys

def bak(obj):
	print 'Toolbar Button pressed!'
	print obj

class Filepart:
	def __init__(self, textview, position, text):
		self.textview = textview

		buffer = self.get_buffer()
		self.tag = buffer.create_tag(None)

		self.start_mark = buffer.create_mark(None, position, True)
		anchor = buffer.create_child_anchor(position)
		buffer.insert(position, '\n')

		self.start_text_mark = buffer.create_mark(None, position, True)
		buffer.insert(position, text[:-1])
		end_text_mark = buffer.create_mark(None, position, True)
		buffer.insert(position,'\n')
		self.end_text_mark = buffer.create_mark(None, buffer.get_iter_at_mark(end_text_mark), False)

		buffer.delete_mark(end_text_mark)
		self.end_mark = buffer.create_mark(None, position, True)

		self._setup_widgets(anchor)
		self._setup_tag_properties()
		self._reapply_tags()

	def _setup_widgets(self, anchor):
		pass
	
	def _setup_tag_properties(self):
		pass

	def _reapply_tags(self):
		buffer = self.get_buffer()
		buffer.remove_all_tags(self.start_iter(), self.end_iter())
		# HACK Widgettag shouldnt be anonymous
		widgettag = buffer.create_tag(None, editable = False, background = 'grey', weight = pango.WEIGHT_BOLD)
		endtag = buffer.create_tag(None, editable = False)
		buffer.apply_tag(widgettag, self.start_iter(), self.start_text_iter())
		buffer.apply_tag(self.tag, self.start_text_iter(), self.end_iter())
		buffer.apply_tag(endtag, self.end_text_iter(), self.end_iter())
	
	def start_iter(self):
		return self.get_buffer().get_iter_at_mark(self.start_mark)

	def start_text_iter(self):
		return self.get_buffer().get_iter_at_mark(self.start_text_mark)

	def end_text_iter(self):
		return self.get_buffer().get_iter_at_mark(self.end_text_mark)
	
	def end_iter(self):
		return self.get_buffer().get_iter_at_mark(self.end_mark)

	def get_buffer(self):
		return self.textview.get_buffer()


class Filepart_with_Button(Filepart):
	def _setup_widgets(self, anchor):
		self.button = gtk.Button()
		self.textview.add_child_at_anchor(self.button, anchor)

	def _get_labeltext(self):
		pass
	
	def _update_buttonlabel(self):
		self.button.set_label(self._get_labeltext())


class CommonFilepart(Filepart_with_Button):
	def __init__(self, textview, position, text):
		Filepart_with_Button.__init__(self, textview, position, text)
		self.button.connect('clicked', self.toggle_hide, None)
		self.hidden = False;
		self.toggle_hide()

	def _setup_tag_properties(self):
		self.tag.set_property('editable', False)

	def _get_labeltext(self):
		if self.hidden:
			return 'Show unchanged part'
		else:
			return 'Hide unchanged part'
	
	def hide(self):
		self.hiddentext = self.get_buffer().get_text(self.start_text_iter(), self.end_text_iter())
		self.get_buffer().delete(self.start_text_iter(), self.end_text_iter())
	
	def show(self):
		self.get_buffer().insert(self.start_text_iter(), self.hiddentext)
		self.hiddentext = None
		self._reapply_tags()
	
	def toggle_hide(self, widget=None, data=None):
		self.hidden = not self.hidden
		self._update_buttonlabel()
		if self.hidden:
			self.hide()
		else:
			self.show()


class OldFilepart(Filepart):
	def __init__(self, textview, position, text):
		Filepart.__init__(self, textview, position, text)
		self.remove = False

	def _setup_widgets(self, anchor):
		button = gtk.Button('Remove this part')
		button.connect('clicked', self.toggle_remove)
		self.textview.add_child_at_anchor(button, anchor)
	
	def _setup_tag_properties(self):
		self.tag.set_property('editable', True)
		self.tag.set_property('foreground', 'green')
	
	def toggle_remove(self, widget=None, data=None):
		self.remove = not self.remove
		self.tag.set_property('strikethrough', self.remove)
				

class NewFilepart(Filepart):
	def __init__(self, textview, position, text):
		Filepart.__init__(self, textview, position, text)
		self.insert = False

	def _setup_widgets(self, anchor):
		button = gtk.Button('Include this part')
		button.connect('clicked', self.toggle_insert)
		self.textview.add_child_at_anchor(button, anchor)
	
	def _setup_tag_properties(self):
		self.tag.set_property('editable', True)
		self.tag.set_property('foreground', 'red')
		self.tag.set_property('strikethrough', True)

	def toggle_insert(self, widget=None, data=None):
		self.insert = not self.insert
		self.tag.set_property('strikethrough', not self.insert)


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
		CommonFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'USE="-*"\n\n')
		OldFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'ACCEPTED_KEYWORDS="~x86"\n# No risk, no fun!\n')
		NewFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'ACCEPTED_KEYWORDS="x86"\n# Play it safe.\n')
		self.window.show_all()


window = MergeWindow()
gtk.main()

# vim:ts=4 sw=4 noet:
