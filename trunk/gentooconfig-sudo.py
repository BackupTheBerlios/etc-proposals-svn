#!/usr/bin/env python

import gtk
import sys
import os

class PasswordDialog(gtk.Dialog):
	
	def __init__(self, parent=None):
		gtk.Dialog.__init__(self, "Password", parent, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
		hbox = gtk.HBox(False, 8)
		hbox.set_border_width(8)
		self.vbox.pack_start(hbox, False, False, 0)
		stock = gtk.image_new_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
		hbox.pack_start(stock, False, False, 0)		
		label = gtk.Label('user password:')
		hbox.pack_start(label, False, False, 0)		
		self.entered_password = gtk.Entry();
		self.entered_password.set_visibility(False)
		hbox.pack_start(self.entered_password, False, False, 0)

def sudo_start():
	dialog = PasswordDialog()
	dialog.show_all()
	if dialog.run() == gtk.RESPONSE_OK:
		pw = dialog.entered_password.get_text()
		dialog.destroy()
		(process_in, process_out) = os.popen2('sudo -p "" -S "%s/gentooconfig.py" --display "%s"' % (os.path.realpath(os.path.dirname(sys.argv[0])), os.environ['DISPLAY']))
		process_out.close()
		process_in.write(pw)
		process_in.close()
	else:
		raise Exception('user aborted')

def direct_start():
	return '"%s/gentooconfig.py"' % (os.path.realpath(os.path.dirname(sys.argv[0])))
	
if os.getuid() == 0:
	direct_start()
else:
	sudo_start()

# vim:ts=4 sw=4 noet:
