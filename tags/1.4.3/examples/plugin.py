#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# plugin samplecode

import etcproposals.etcproposals_info as info
import gtk, subprocess, os

class OptionWidget(object):
    @staticmethod
    def get_optionwidget_from_option(option):
        if option.hide_in_gui:
            return None
        if option.optiontype == 'toggle':
            return ToggleOptionWidget(option)
        elif option.optiontype == 'radio':
            return RadioOptionWidget(option)
        return None


class ToggleOptionWidget(gtk.CheckButton):
    def __init__(self, toggleoption):
        gtk.CheckButton.__init__(self, toggleoption.description)
        self.toggleoption = toggleoption

    def get_commandline_text(self):
        if self.get_active():
            return self.toggleoption.command   
        return None


class RadioOptionWidget(gtk.Frame):
    def __init__(self, radiooption):
        gtk.Frame.__init__(self, radiooption.name)
        self.vbox = gtk.VBox()
        self.vbox.add(gtk.Label(radiooption.description))
        lastoption = None
        for option in radiooption:
            widget = gtk.RadioButton(lastoption, option.description)
            widget.command = option.command
            lastoption = widget
            self.vbox.add(widget)
        self.add(self.vbox)

    def get_commandline_text(self):
        return ''.join((widget.command for widget in self.vbox if widget.__dict__.has_key('command') and widget.get_active()))


class LauncherWindow(gtk.Window):
    def __init__(self, options, versions):
        gtk.Window.__init__(self)
        self.set_title('etc-proposal launcher')
        self.set_position(gtk.WIN_POS_CENTER)

        self.optionwidgets = []

        notebook = self._build_notebook(options, versions)
        launch_button = gtk.Button('Start')
        vbox = gtk.VBox()
        vbox.pack_start(notebook, True, True, 0)
        vbox.pack_start(launch_button, False, False, 0)
        self.add(vbox)

        self.connect('destroy', lambda *w: gtk.main_quit())
        launch_button.connect('clicked', self.on_launchbutton_clicked)
        self.set_size_request(600, 400)
        self.show_all()

    def _build_notebook(self, options, versions):
        notebook = gtk.Notebook()
        options_page = self._build_options_page(options)
        notebook.append_page(options_page, gtk.Label('Options'))
        versions_page = self._build_versions_page(versions)
        notebook.append_page(versions_page, gtk.Label('Versions'))
        return notebook
    
    def _build_options_page(self, options):
        vbox = gtk.VBox()
        for option in options:
            widget = OptionWidget.get_optionwidget_from_option(option)
            if not widget == None:
                self.optionwidgets.append(widget)
                vbox.pack_start(widget, False, False, 0)
        return vbox
        
    def _build_versions_page(self, versions):
        return gtk.Label(versions.prettify())

    def on_launchbutton_clicked(self, button):
        args = [info.COMMAND]
        args.extend((widget.get_commandline_text() for widget in self.optionwidgets if not widget.get_commandline_text()==None))
        if os.getuid()==0 or not info.MUST_RUN_AS_ROOT:
            subprocess.Popen(args)
        else:
            msg_opt = "-m 'etc-proposals allows you to update your configuration files. Please type in the administrative password'"
            subprocess.Popen(['gksu', msg_opt, ' '.join(args)])
        

win = LauncherWindow(info.OPTIONS, info.VERSIONS)
gtk.main()
