#!/usr/bin/python -O

import getopt
import gtk
import pango
import sys

def bak(obj):
	print 'Toolbar Button pressed!'
	print obj

class Singleton(object):
	__instance = None
	@classmethod
	def get_instance(cls):
		if cls.__instance == None:
			__instance = GentooconfigApplication()
		return __instance

class Filepart(object):
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
		buffer.apply_tag(widgettag, self.start_iter(), self._start_text_iter())
		buffer.apply_tag(self.tag, self._start_text_iter(), self.end_iter())
		buffer.apply_tag(endtag, self._end_text_iter(), self.end_iter())
	
	def start_iter(self):
		return self.get_buffer().get_iter_at_mark(self.start_mark)

	def _start_text_iter(self):
		return self.get_buffer().get_iter_at_mark(self.start_text_mark)

	def _end_text_iter(self):
		return self.get_buffer().get_iter_at_mark(self.end_text_mark)
	
	def end_iter(self):
		return self.get_buffer().get_iter_at_mark(self.end_mark)

	def _containing_text(self):
		return self.get_buffer().get_text(self._start_text_iter(), self._end_text_iter())
	
	def file_text(self):
		return self._containing_text() + '\n'

	def get_buffer(self):
		return self.textview.get_buffer()


class Filepart_with_Button(Filepart):
	def _setup_widgets(self, anchor):
		self.button = gtk.Button()
		self.button.connect('clicked', self.on_button_clicked, None)
		self.textview.add_child_at_anchor(self.button, anchor)

	def _get_labeltext(self):
		pass
	
	def _update_buttonlabel(self):
		self.button.set_label(self._get_labeltext())

	def on_button_clicked(self, widget=None, data=None):
		pass


class CommonFilepart(Filepart_with_Button):
	def __init__(self, textview, position, text):
		Filepart_with_Button.__init__(self, textview, position, text)
		self.hidden = False;
		self.on_button_clicked()

	def _setup_tag_properties(self):
		self.tag.set_property('editable', False)

	def _get_labeltext(self):
		if self.hidden:
			return 'Show unchanged part'
		return 'Hide unchanged part'
	
	def file_text(self):
		if self.hidden:
			return self.hiddentext + '\n'
		return self._containing_text() + '\n'
	
	def hide(self):
		self.hiddentext = self._containing_text()
		self.get_buffer().delete(self._start_text_iter(), self._end_text_iter())
		self.get_buffer().insert(self._start_text_iter(),'[...]')
	
	def show(self):
		self.get_buffer().delete(self._start_text_iter(), self._end_text_iter())
		self.get_buffer().insert(self._start_text_iter(), self.hiddentext)
		self.hiddentext = None
		self._reapply_tags()
	
	def on_button_clicked(self, widget=None, data=None):
		self.hidden = not self.hidden
		self._update_buttonlabel()
		if self.hidden:
			self.hide()
		else:
			self.show()


class OldFilepart(Filepart_with_Button):
	def __init__(self, textview, position, text):
		Filepart_with_Button.__init__(self, textview, position, text)
		self.remove = False
		self._update_buttonlabel()

	def _setup_tag_properties(self):
		self.tag.set_property('editable', True)
		self.tag.set_property('foreground', 'green')
	
	def _get_labeltext(self):
		if self.remove:
			return 'Dont remove this part found in local config'
		return 'Remove this part found in local config'

	def file_text(self):
		if self.remove:
			return ''
		return self._containing_text() + '\n'

	def on_button_clicked(self, widget=None, data=None):
		self.remove = not self.remove
		self._update_buttonlabel()
		self.tag.set_property('strikethrough', self.remove)
				

class NewFilepart(Filepart_with_Button):
	def __init__(self, textview, position, text):
		Filepart_with_Button.__init__(self, textview, position, text)
		self.insert = False
		self._update_buttonlabel()
	
	def _setup_tag_properties(self):
		self.tag.set_property('editable', True)
		self.tag.set_property('foreground', 'red')
		self.tag.set_property('strikethrough', True)

	def file_text(self):
		if self.insert:
			return self._containing_text() + '\n'
		return ''

	def _get_labeltext(self):
		if self.insert:
			return 'Dont insert this part found in package config'
		return 'Insert this part found in package config'

	def on_button_clicked(self, widget=None, data=None):
		self.insert = not self.insert
		self._update_buttonlabel()
		self.tag.set_property('strikethrough', not self.insert)

class UIFactory(gtk.UIManager):
	__instance = None
	def __init__(self):
		gtk.UIManager.__init__(self)
		ag = gtk.ActionGroup('Actions')
		quit = gtk.Action('Quit', 'Quit', 'Quit the App', gtk.STOCK_QUIT)
		ag.add_action(quit)
		quit = gtk.Action('File', 'File', 'File', None)
		ag.add_action(quit)
		self.insert_action_group(ag,0)
		self.add_ui_from_file('./gentooconfig_ui.xml')
	
	@classmethod
	def get_instance(cls):
		if cls.__instance == None:
			__instance = UIFactory()
		return __instance


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
	

class MergeWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)
		vbox = gtk.VBox()
		self.menubar = UIFactory.get_instance().get_widget('/MenuBar')
		self.toolbar = MergeToolbar()
		self.textview = gtk.TextView()
		self.statusbar = gtk.Statusbar()
		vbox.pack_start(self.menubar, False, False);
		vbox.pack_start(self.toolbar, False, False);
		vbox.pack_start(self.textview);
		vbox.pack_start(self.statusbar, False, False);
		self.add(vbox)
		context = self.statusbar.get_context_id('statusbar')
		self.statusbar.push(context, 'Merging file /etc/._cfg000_make.conf')
		CommonFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'USE="-*"\n\n')
		OldFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'ACCEPTED_KEYWORDS="~x86"\n# No risk, no fun!\n')
		NewFilepart(self.textview, self.textview.get_buffer().get_end_iter(), 'ACCEPTED_KEYWORDS="x86"\n# Play it safe.\n')
		self.show_all()

class GentooconfigApplication(Singleton):
	def __init__(self):
		window = MergeWindow()
		gtk.main()
	
	def get_actiongroup(self):
		actiongroup = gtk.ActionGroup()
		actionlist =[
			('Quit', 'Quit', 'Quit', None)
		]
		return actiongroup.add_actions(actionlist)


GentooconfigApplication.get_instance()
# vim:ts=4 sw=4 noet:
