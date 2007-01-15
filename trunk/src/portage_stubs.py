#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# based on gentoo portage 2.1.1, Copyright 1998-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import shlex, string, os

# portage constants

VDB_PATH                = "var/db/pkg"

PROFILE_PATH            = "/etc/make.profile"

MAKE_CONF_FILE          = "/etc/make.conf"
MAKE_GLOBALS_FILE       = "/etc/make.globals"
MAKE_DEFAULTS_FILE      = PROFILE_PATH + "/make.defaults"

# color output stuff

class CmdLineColorizer(object):
    def __init__(self):
        ESC_SEQ = "\x1b["
        self.colorcodes ={ "reset": ESC_SEQ + "39;49;00m",
            "bold" : ESC_SEQ + "01m",
            "faint" : ESC_SEQ + "02m",
            "standout" : ESC_SEQ + "03m",
            "underline" : ESC_SEQ + "04m",
            "blink" : ESC_SEQ + "05m",
            "overline" : ESC_SEQ + "06m"}

        def AnsiColorCodeGenerator(start, stop, ZeroOne = False):
            for x in xrange(start, stop):
                yield "%im" % x
                yield "%i;01m" % x
        ansi_color_codes = AnsiColorCodeGenerator(30, 38)

        rgb_ansi_colors = ['0x000000', '0x555555', '0xAA0000', '0xFF5555', '0x00AA00',
            '0x55FF55', '0xAA5500', '0xFFFF55', '0x0000AA', '0x5555FF', '0xAA00AA',
            '0xFF55FF', '0x00AAAA', '0x55FFFF', '0xAAAAAA', '0xFFFFFF']

        for rgb_ansi_color in rgb_ansi_colors:
            self.colorcodes[rgb_ansi_color] = ESC_SEQ + ansi_color_codes.next()

        self.colorcodes["black"]     = self.colorcodes["0x000000"]
        self.colorcodes["darkgray"]  = self.colorcodes["0x555555"]
        self.colorcodes["red"]       = self.colorcodes["0xFF5555"]
        self.colorcodes["darkred"]   = self.colorcodes["0xAA0000"]
        self.colorcodes["green"]     = self.colorcodes["0x55FF55"]
        self.colorcodes["darkgreen"] = self.colorcodes["0x00AA00"]
        self.colorcodes["yellow"]    = self.colorcodes["0xFFFF55"]
        self.colorcodes["brown"]     = self.colorcodes["0xAA5500"]
        self.colorcodes["blue"]      = self.colorcodes["0x5555FF"]
        self.colorcodes["darkblue"]  = self.colorcodes["0x0000AA"]
        self.colorcodes["fuchsia"]   = self.colorcodes["0xFF55FF"]
        self.colorcodes["purple"]    = self.colorcodes["0xAA00AA"]
        self.colorcodes["turquoise"] = self.colorcodes["0x55FFFF"]
        self.colorcodes["teal"]      = self.colorcodes["0x00AAAA"]
        self.colorcodes["white"]     = self.colorcodes["0xFFFFFF"]
        self.colorcodes["lightgray"] = self.colorcodes["0xAAAAAA"]
        self.colorcodes["darkyellow"] = self.colorcodes["brown"]
        self.colorcodes["fuscia"]     = self.colorcodes["fuchsia"]
        self.colorcodes["white"]      = self.colorcodes["bold"]
        print self.colorcodes
        self.use_colors = True

    def colorize(self, color_key, text):
        if self.use_colors:
            return self.colorcodes[color_key] + text + self.colorcodes["reset"]
        else:
            return text

colorcodes = CmdLineColorizer()


class PortageInterface(object):
    @staticmethod
    def get_config_protect():
        make_conf_settings = PortageInterface._portage_utils_getconfig(MAKE_CONF_FILE)
        make_globals_settings = PortageInterface._portage_utils_getconfig(MAKE_GLOBALS_FILE)
        make_defaults_settings = PortageInterface._portage_utils_getconfig(MAKE_DEFAULTS_FILE)
        config_protect = os.environ['CONFIG_PROTECT']
        for config_settings in [make_defaults_settings, make_globals_settings, make_conf_settings]:
            if config_settings.has_key('CONFIG_PROTECT'):
                config_protect = config_protect + ' ' + config_settings['CONFIG_PROTECT'][1:-1]
        return config_protect.split()

    @staticmethod
    def _portage_utils_getconfig(mycfg):
        def parser_state_generator():
            while True:
                for state in ['key', 'equals', 'value']:
                    yield state
        mykeys = {}
        f = open(mycfg,'r')
        lex = shlex.shlex(f)
        lex.wordchars = string.digits+string.letters+"~!@#$%*_\:;?,./-+{}"     
        lex.quotes = "\"'"
        parser_states = parser_state_generator()
        while True:
            token=lex.get_token()
            parser_state = parser_states.next()
            if token=='' or (parser_state == 'equals' and not token =='='):
                break
            if parser_state == 'key':
                key = token
            if parser_state == 'value':
                mykeys[key]=token.replace("\\\n","")
        return mykeys
    
    @staticmethod
    def colorize(color_key, text):
        return colorcodes.colorize(color_key, text)

    @staticmethod
    def nocolor():
        colorcodes.use_colors = False

__all__ = ['PortageInterface']
