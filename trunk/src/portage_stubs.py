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

# portage utils stuff
class PortageUtils(object):
    @staticmethod
    def getconfig(mycfg):
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
    def get_config_protect():
        make_conf_settings = PortageUtils.getconfig(MAKE_CONF_FILE)
        make_globals_settings = PortageUtils.getconfig(MAKE_GLOBALS_FILE)
        make_defaults_settings = PortageUtils.getconfig(MAKE_DEFAULTS_FILE)
        config_protect = os.environ['CONFIG_PROTECT']
        for config_settings in [make_defaults_settings, make_globals_settings, make_conf_settings]:
            if config_settings.has_key('CONFIG_PROTECT'):
                config_protect = config_protect + ' ' + config_settings['CONFIG_PROTECT'][1:-1]
        return config_protect.split()


# color output stuff
class CmdLineColorizer(object):
    def __init__(self):
        ESC_SEQ = "\x1b["
        self.colorcodes ={ 'reset': ESC_SEQ + '39;49;00m'}
        def AnsiColorCodeGenerator(start, stop, formatstring = '%02im'):
            for x in xrange(start, stop + 1):
                yield ESC_SEQ + formatstring % x

        generated_codes = AnsiColorCodeGenerator(1,6)
        for colorcode in ['bold', 'faint', 'standout', 'underline', 'blink', 'overline']:
            self.colorcodes[colorcode] = generated_codes.next()
        generated_codes = AnsiColorCodeGenerator(30,37)
        for colorcode in ['0x000000', '0xAA0000', '0x00AA00', '0xAA5500', '0x0000AA', '0xAA00AA', '0x00AAAA', '0xAAAAAA']:
            self.colorcodes[colorcode] = generated_codes.next()
        generated_codes = AnsiColorCodeGenerator(30,37, '%02i;01m')
        for colorcode in ['0x555555', '0xFF5555', '0x55FF55', '0xFFFF55', '0x5555FF', '0xFF55FF', '0x55FFFF', '0xFFFFFF']:
            self.colorcodes[colorcode] = generated_codes.next()
        for alias in {'black' : '0x000000', 'darkgray' : '0x555555', 'red' : '0xFF5555', 'darkred' : '0xAAAAAA',
            'green' : '0x55FF55', 'darkgreen' : '0x00AA00', 'yellow' : '0xFF5555', 'brown' : '0xAA5500',
            'blue' : '0x5555FF', 'darkblue' : '0x0000AA', 'fuchsia' : '0xFF55FF', 'purple' : '0xAA00AA',
            'turquoise' : '0x55FFFF', 'teal' : '0x00AAAA', 'white' : '0xFFFFFF', 'lightgray' : '0xAAAAAA',
            'darkyellow' : 'brown', 'fuscia' : 'fuchsia'}.iteritems():
            self.colorcodes[alias[0]] = self.colorcodes[alias[1]]
        self.use_colors = True

    def colorize(self, color_key, text):
        if self.use_colors:
            return self.colorcodes[color_key] + text + self.colorcodes["reset"]
        else:
            return text

colorizer = CmdLineColorizer()


class PortageInterface(object):
    @staticmethod
    def get_config_protect():
		return PortageUtils.get_config_protect()

    @staticmethod
    def colorize(color_key, text):
        return colorizer.colorize(color_key, text)

    @staticmethod
    def nocolor():
        colorizer.use_colors = False

__all__ = ['PortageInterface']
