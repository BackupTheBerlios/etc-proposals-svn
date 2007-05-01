#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# based on gentoo portage 2.1.1, Copyright 1998-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import subprocess, errno

# helper needed because PyQt seems to cause interrupted system calls
def get_command_output_iterator(command_and_args):
    outpipe = subprocess.Popen(command_and_args, shell=False, stdout=subprocess.PIPE).stdout
    eof = False
    while not eof:
        try:
            for line in outpipe.readlines():
                yield line
            eof = True
        except (OSError, IOError), e:
            if e.errno != errno.EINTR:
                raise e

__ALL__=[get_command_output_iterator]
