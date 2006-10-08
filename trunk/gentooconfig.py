#!/usr/bin/env python

import getopt
import gtk
import sys

def hello(*args):
    print "Button pressed!"
    
def quit(*args):
	gtk.main_quit()
	
window = gtk.Window()
window.connect("destroy", quit)
window.show_all()
gtk.main()

# vim:ts=4 sw=4 noet:
