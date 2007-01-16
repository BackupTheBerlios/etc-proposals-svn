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


class PortageInterface(object):
    @staticmethod
    def get_config_protect():
        return PortageUtils.get_config_protect()


__all__ = ['PortageInterface']
