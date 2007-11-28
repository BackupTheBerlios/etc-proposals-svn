#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a little shell to integrate modified configs, post-emerge

__author__ = 'Björn Michaelsen' 
__version__ = '1.3'
__date__ = '2007-06-06'

import cmd, difflib, os, os.path, re, tempfile
from etcproposals.etcproposals_lib import *
from etcproposals.etcproposals_lib import __version__ as __libversion__


class NotOnChangeException(Exception):
    "happens when a operation needs a current change and there is None"
    pass

class UnknownChangeException(Exception):
    "happens when an operation should be performed on a change that cant be found"
    pass


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


class EtcProposalChangeShellDecorator(EtcProposalChange):
    def get_status_description(self, colorizer):
        if not self.touched:
            return '---'
        return {True : colorizer.colorize('green','use'), False : colorizer.colorize('red','zap')}[self.merge]

    def get_ws_cvs_description(self, colorizer):
        ws_text = {True : 'WSp', False : ''}[self.is_whitespace_only()]
        cvs_text = {True : 'CVS', False : ''}[self.is_cvsheader()]
        unmodified_text = {True : '!mod', False : ''}[self.is_unmodified()]
        return colorizer.colorize('turquoise', ' '.join([ws_text, cvs_text, unmodified_text]).center(8))

    def get_listing_description(self, colorizer):
        return '(%s) (%s) %s' % (
            self.get_status_description(colorizer),
            self.get_ws_cvs_description(colorizer).center(8),
            self.get_id())

    def get_id(self):
        affected_lines = self.get_affected_lines()
        return '%s:%d-%d(%d)' % (
            self.get_file_path(),
            affected_lines[0],
            affected_lines[1],
            self.get_revision())
        
    def get_complete_description(self, colorizer):
        affected_lines = self.get_affected_lines()
        result = list()
        result.append('\n-------- %s\n' % self.get_listing_description(colorizer))
        result.append('This change proposes to %s content at lines %d-%d in file %s\n' % 
                (self.get_action(), affected_lines[0], affected_lines[1], self.get_file_path()))
        result.extend(self._get_colored_differ_lines(colorizer))
        result.append('-------- %s' % self.get_listing_description(colorizer))
        return ''.join(result)

    def _get_colored_differ_lines(self, colorizer):
        differ = difflib.Differ()
        differ_lines = list()
        for line in differ.compare(self.get_base_content(), self.get_proposed_content()):
            if line.startswith('+'):
                differ_lines.append(colorizer.colorize('green', line))
            elif line.startswith('-'):
                differ_lines.append(colorizer.colorize('red', line))
            elif line.startswith('?'):
                differ_lines.append(colorizer.colorize('faint', ' ' + line[1:]))
        return differ_lines


class EtcProposalShellDecorator(EtcProposal):
    def get_status_description(self):
        self._assure_changes_exists()
        return {True : '(finished)', False : '(        )'}[self.is_finished()]

    def get_listing_description(self, colorizer):
        return '%s %s(%d)' % (self.get_status_description(),self.get_file_path(), self.get_revision())

    # Being picky, we only want decorated Changes
    def _create_change(self, opcode):
        return EtcProposalChangeShellDecorator(opcode, self)


class EtcProposalsShellDecorator(EtcProposals):
    def __init__(self, cmdline):
        EtcProposals.__init__(self)
        self.cmdline = cmdline

    # Being picky, we only want decorated Proposals
    def _create_proposal(self, proposal_path, current_file_callback):
        if not current_file_callback is None: current_file_callback()
        return EtcProposalShellDecorator(proposal_path, self)


class EtcProposalsConfigShellDecorator(EtcProposalsConfig):
    def Colorize(self):
        try:
            return self.parser.getboolean('Shell', 'Colorize')
        except Exception:
            return False

    def EditCommand(self):
        try:
            return self.parser.get('Shell', 'EditCommand', True)
        except Exception, e:
            print e
        if not os.environ.has_key('EDITOR'):
            editor = 'nano'
        else:
            editor = os.environ['EDITOR']
        if editor.count('nano') > 0:
            return '%s +%%(linenumber)d,0 "%%(filename)s"' % os.environ['EDITOR']
        elif editor.count('vi') > 0:
            return '%s -c %%(linenumber)d "%%(filename)s"' % os.environ['EDITOR']
        elif editor.count('emacs') > 0:
            return '%s +%%(linenumber)d "%%(filename)s"' % os.environ['EDITOR']
        else:
            return '%s "%%(filename)s"' % os.environ['EDITOR']

    def DiffCommand(self):
        try:
            return self.parser.get('Shell', 'DiffCommand', True)
        except Exception:
            return 'diff -u "%(file1)s" "%(file2)s"'

    def StartupCommands(self):
        try:
            return self.parser.get('Shell', 'StartupCommands').split(';')
        except Exception:
            return []


class CmdLineCommand(object):
    def __init__(self, cmdline):
        self.cmdline = cmdline
        self.commandname = self.__class__.__name__[:-7]

    def do_cmd(self, args):
        pass

    def help_cmd(self):
        return self.__doc__

    def complete_cmd(self, text, line, begidx, endidx):
        pass

    def complete_from_list(self, text, subcommandlist):
        if text == '':
            return subcommandlist
        return [subcommand for subcommand in subcommandlist 
            if subcommand.startswith(text)]


class ListCommand(CmdLineCommand):
    """SYNOPSIS:
    list changes | proposals | files
    list

DESCRIPTION:
    The list command lists all files, proposals or changes currently
    available for update. It also shows, which changes were chosen to be
    use or zapped.

NOTE:
    The list of changes might change, if you set a change to use or zap.
    For example, if there are two update proposals for one file, proposing
    to change the same line in the same way, 'use' on the first change
    will make the second disappear (as it is not a change at all anymore)."""
    def list_changes(self):
        print 'proposed changes:'
        for change in self.cmdline.changesets['all']():
            print change.get_listing_description(self.cmdline.colorizer)
        print

    def list_proposals(self):
        print 'update proposals:'
        for proposal in self.cmdline.proposals:
            print proposal.get_listing_description(self.cmdline.colorizer)
        print
    
    def list_files(self):
        print 'List of files with update proposals:'
        for filename in self.cmdline.proposals.get_files():
            print self.cmdline.colorizer.colorize('white', filename)
        print

    def complete_cmd(self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['changes', 'proposals', 'files'])

    def do_cmd(self, args):
        list_cmds = {'' : self.list_changes,
                'changes' : self.list_changes,
                'proposals' : self.list_proposals,
                'files' : self.list_files}
        try:
            list_cmds[args.strip()]()
        except KeyError:
            print 'list: Sorry, I dont know "%s".' % args


class NextCommand(CmdLineCommand):
    """SYNOPSIS:
    next change | proposal | file | dir
    next
    n change | proposal | file | dir
    n

DESCRIPTION:
    The next command is used to iterate through the proposed changes.
    If no argument is given, the command navigates to the next change."""

    def skip_changes(self, changes_to_skip):
            while self.cmdline.current_change in changes_to_skip:
                self.cmdline.next_change()

    def complete_cmd(self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['change', 'proposal', 'file', 'dir'])

    def do_cmd(self, args):
        next_cmds = {'' : self.cmdline.next_change,
                'change' : self.cmdline.next_change,
                'proposal' : lambda: self.skip_changes(self.cmdline.changesets['proposal']()),
                'file' : lambda: self.skip_changes(self.cmdline.changesets['file']()),
                'dir' : lambda: self.skip_changes(self.cmdline.changesets['dir']())}
        try:
            next_cmds[args.strip()]()
        except KeyError:
            print 'next: Sorry, I dont know "%s".' % args
            return
        except NotOnChangeException:
            self.cmdline.next_change()
        if self.cmdline.current_change:
            self.show_change()
        self.cmdline.update_prompt()


class ShowCommand(CmdLineCommand):
    """SYNOPSIS:
    show change | proposal | file | dir | all | whitespace | cvsheader | unmodified
    show

DESCRIPTION:
    The show command is used to use the current change/proposal, all 
    proposals for the current file or dir or all dirs, which are not
    If no argument is given, the command redisplays the current change."""
    def show_changes(self, changes):
        print '\n'.join([change.get_complete_description(self.cmdline.colorizer) for change in changes])

    def complete_cmd(self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['change', 'proposal', 'file', 'dir', 'all', 'whitespace', 'cvsheader', 'unmodified'])

    def do_cmd(self, args):
        try:
            self.show_changes(self.cmdline.changesets[args.strip()]())
        except KeyError:
            print 'show: Sorry, I dont know "%s".' % args
        except NotOnChangeException:
            print 'show: There is no change selected right now.'


class ZapCommand(CmdLineCommand):
    """SYNOPSIS:
    zap change | proposal | file | dir | all | whitespace | cvsheader | unmodified
    zap
    z change | proposal | file | dir | all | whitespace | cvsheader | unmodified
    z

DESCRIPTION:
    The zap command is used to discard the current change/proposal, all 
    proposals for the current file or dir or all dirs, which are not
    yet already marked 'use' or 'zap' and proceeds.
    If no argument is given, the command zaps just the current change."""
    def zap_changes(self, changes):
        [change.zap() for change in changes if not change.touched]

    def complete_cmd (self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['change', 'proposal', 'file', 'dir', 'all', 'whitespace', 'cvsheader', 'unmodified'])

    def do_cmd(self, args):
        try:
            self.zap_changes(self.cmdline.changesets[args.strip()]())
        except KeyError:
            print 'zap: Sorry, I dont know "%s".' % args
            return
        except NotOnChangeException:
            print 'zap: There is no change selected right now.'
            return
        self.cmdline.hop_on_and_show(args)


class UseCommand(CmdLineCommand):
    """SYNOPSIS:
    use change | proposal | file | dir | all | whitespace | cvsheader | unmodified
    use
    u change | proposal | file | dir | all | whitespace | cvsheader | unmodified
    u

DESCRIPTION:
    The use command is used to use the current change/proposal, all 
    proposals for the current file or dir or all dirs, which are not
    yet already marked 'zap' or 'use' and proceeds.
    If no argument is given, the command uses just the current change."""
    def use_changes(self, changes):
        [change.use() for change in changes if not change.touched]

    def complete_cmd(self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['change', 'proposal', 'file', 'dir', 'all', 'whitespace', 'cvsheader', 'unmodified'])

    def do_cmd(self, args):
        try:
            self.use_changes(self.cmdline.changesets[args.strip()]())
        except KeyError:
            print 'use: Sorry, I dont know "%s".' % args
            return
        except NotOnChangeException:
            print 'use: There is no change selected right now.'
            return
        self.hop_on_and_show(args)


class UndoCommand(CmdLineCommand):
    """SYNOPSIS:
    undo change | proposal | file | dir | all |whitespace | cvsheader | unmodified

DESCRIPTION:
    The undo command resets the selections made to 'use' or 'zap' the
    current change/proposal, all proposals for the current file or dir or
    all changes in all dirchanges in all dirs. 
    If no argument is given, the command just undos the current change."""
    def undo_changes(self, changes):
        [change.undo() for change in changes]

    def complete_cmd(self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['change', 'proposal', 'file', 'dir', 'all', 'whitespace', 'cvsheader', 'unmodified'])
    
    def do_cmd(self, args):
        try:
            self.undo_changes(self.cmdline.changesets[args.strip()]())
        except KeyError:
            print 'undo: Sorry, I dont know "%s".' % args
            return
        except NotOnChangeException:
            print 'undo: Sorry, no change to undo selected.'
        self.cmdline.update_prompt()


class ReloadCommand(CmdLineCommand):
    """SYNOPSIS:
    reload

DESCRIPTION:
    The reload command rescans the filesystems for update proposals.
    The current selections about using or zapping changes are retained,
    if possible."""

    def do_cmd(self, args):
        if args.strip() == '':
            self.cmdline.reload()
        else:
            print 'reload: Sorry, I dont know "%s".' % args
            return


class DiffCommand(CmdLineCommand):
    """SYNOPSIS:
    diff change | proposal
    diff

DESCRIPTION:
    The diff command shows the differences for this change or proposal
    in an external diff tool. It selects the tool by reading the DIFF
    enviroment variable"""
    def external_diff_on_stringlists(self, a, b, a_name, b_name):
        (fd_a, filename_a) = tempfile.mkstemp('', a_name + '___')
        (fd_b, filename_b) = tempfile.mkstemp('', b_name + '___')
        os.write(fd_a, ''.join(a))
        os.write(fd_b, ''.join(b))
        os.close(fd_a)
        os.close(fd_b)
        os.system(self.cmdline.config.DiffCommand() % {
            'file1' : filename_a,
            'file2' : filename_b})
        for file in [filename_a, filename_b]:
            try:
                os.unlink(file)
            except OSError:
                pass

    def diff_change(self):
        file_path = self.cmdline.current_change.get_file_path()
        self.external_diff_on_stringlists(
                self.cmdline.current_change.get_base_content(),
                self.cmdline.current_change.get_proposed_content(),
                file_path + '_BASE',
                file_path + '_PROPOSAL')

    def diff_proposal(self):
        proposal = self.cmdline.current_change.proposal
        self.external_diff_on_stringlists(
                proposal.get_base_content(),
                proposal.get_proposed_content(),
                proposal.get_file_path() + '_BASE',
                proposal.get_file_path() + '_PROPOSAL')

    def complete_cmd(self, text, line, begidx, endidx):
        return self.complete_from_list(text, ['change', 'proposal'])

    def do_cmd(self, args):
        if self.cmdline.current_change is None:
            print 'diff: There is no change selected right now.'
            return
        diff_cmds = {'' : self.diff_change,
                'change' : self.diff_change,
                'proposal' : self.diff_proposal}
        try:
            diff_cmds[args.strip()]()
        except KeyError:
            print 'diff: Sorry, I dont know "%s".' % args
            return


class EditCommand(CmdLineCommand):
    """SYNOPSIS:
    edit

DESCRIPTION:
    The edit command allows the user to edit the current file. It starts
    an editor with the current file at the start of the current
    change, if possible. When the editor is finished etc-proposals rescans
    the filesystem for proposals and normal use of etc-proposals can
    continue.

NOTE:
    etc-proposals uses the EDITOR enviroment variable to choose the editor
    it starts."""
    def edit(self):
        linenumber = self.cmdline.current_change.get_affected_lines()[0]
        filepath = self.cmdline.current_change.get_file_path()
        os.system(self.cmdline.config.EditCommand() % {'linenumber' :  linenumber, 'filename' : filepath})

    def do_cmd(self, args):
        if self.cmdline.current_change is None:
            print 'edit: There is no change selected right now.'
            return
        self.edit()
        self.cmdline.reload()
        self.cmdline.next_change()
        self.cmdline.update_prompt()


class GotoCommand(CmdLineCommand):
    """SYNOPSIS:
    goto <change> 

DESCRIPTION:
    The goto command is used to jump to a change in the changelist.
    Using tabcompletion makes it actually useful."""
    def goto_change(self, changepromptname):
        search_iter = self.cmdline.proposals.get_all_changes().__iter__()
        try:
            current_search_item = search_iter.next()
            while current_search_item.get_id() != changepromptname:
                current_search_item = search_iter.next()
        except StopIteration:
            raise UnknownChangeException
        self.cmdline.current_change = current_search_item
        self.cmdline.change_iter = search_iter

    def complete_cmd(self, text, line, begidx, endidx):
        try:
            part_to_complete = re.match('goto\s*(.*)',line).groups()[0]
            len_to_complete = len(part_to_complete)
            changenames = (change.get_id()
                for change in self.proposals.get_all_changes())
            matches =  self.complete_from_list(part_to_complete, changenames)
            return [ text + match[len_to_complete:] for match in matches]
        except Exception:
            return []

    def do_cmd(self, args):
        try:
            print args
            self.goto_change(args.strip())
            self.cmdline.update_prompt()
            self.show_change()
        except UnknownChangeException:
            print 'goto: There is no change "%s"' % args


class ApplyCommand(CmdLineCommand):
    """SYNOPSIS:
    apply
DESCRIPTION:
    The apply command merges the changes into the configuration files.
    It only merges proposals, were all changes have been decided upon.
    The merged proposals are removed from the filesystem after they
    have been merged. Its a good idea to check the decisions with the
    'list changes' command before calling 'apply'.

NOTE:
    You dont need to decide on all proposed changes, but if you what to
    merge a change, all other changes from that proposal need to be set
    to either 'zap' or 'use'. If you just want one change from a proposal,
    use the command 'use' on it and then use the command 'zap proposal' to
    discard all other changes from that proposal."""
    def do_cmd(self, args):
        self.proposals.apply(True)
        self.cmdline.current_change = None
        self.cmdline.change_iter = self.proposals.get_all_changes().__iter__()
        self.cmdline.update_prompt()
        if len(self.proposals) == 0 and EtcProposalsConfigShellDecorator().Fastexit():
            print "No proposes left. Exiting."
            raise SystemExit


class QuitCommand(CmdLineCommand):
    """SYNOPSIS:
    quit
    Ctrl-d

DESCRIPTION:
    Quits etc-proposals."""
    def do_quit(self, args):
        raise SystemExit


class EtcProposalsCmdLine(cmd.Cmd):
    COMMANDS = [ EditCommand, QuitCommand, ApplyCommand, GotoCommand,
        UndoCommand, UseCommand, ZapCommand, ListCommand, ReloadCommand,
        DiffCommand ]
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.colorizer = CmdLineColorizer()
        self.config = EtcProposalsConfigShellDecorator()
        if not self.config.Colorize():
            self.colorizer.use_colors = False;
        self.add_commands()
        self.reload()
        self.intro = """Welcome to etc-proposals, a shell for gentoo configuration updates
        shell version: %s
        lib version: %s
        copyright 2006, 2007 Björn Michaelsen, GPL v2
        Type '?' or 'help' to get help or
        type 'n' to start iterating through proposed changes.
""" % (__version__, __libversion__)
    
    def add_commands(self):
        for commandclass in EtcProposalsCmdLine.COMMANDS:
            command = commandclass(self)
            self.__dict__["do_" + command.commandname] = command.do_cmd
            self.__dict__["help_" + command.commandname] = command.help_cmd
            self.__dict__["complete_" + command.commandname] = command.complete_cmd

    def setup_changesets(self):
        self.changesets = {'' : lambda: [self.current_change],
                'change' : lambda: [self.current_change],
                'proposal' : self.get_current_proposal_changes,
                'file' : self.get_current_file_changes,
                'dir' : self.get_current_dir_changes,
                'all' : self.proposals.get_all_changes,
                'whitespace' : self.proposals.get_whitespace_changes,
                'cvsheader' : self.proposals.get_cvsheader_changes,
                'unmodified' : self.proposals.get_unmodified_changes}

    def preloop(self):
        print self.intro
        for command in self.config.StartupCommands():
            self.onecmd(command)
        self.intro = ''

    def reload(self):
        self.proposals = EtcProposalsShellDecorator(self)
        self.setup_changesets()
        self.current_change = None
        self.change_iter = self.proposals.get_all_changes().__iter__()
        self.update_prompt()

    def help_quickstart(self):
        """etc-proposals Quickstart

    etc-proposals is a shell-like tool to merge updates to protected
    configuration files. Its a replacement for etc-update.
        
BASIC USAGE:
    Start iterating through the proposed changes with the 'n' command.
    Use the 'u', 'z' and 'n' commands to either use a proposed change,
    zap a proposed change or to skip to the next change.
    When you reach the end of the list of proposals, type 'list' to
    review your decisions. If you are satisfied, use the command 'apply'
    to merge the changes into the filesystem.

NOTE:
    Sending an empty commandline repeats the last command.
    Also note, that the commandline has history and tab-completion.

VOCABULARY:
    all       - all changes proposed for all files
    file      - one configuration file in CONFIG_PROTECT
                (for example: /etc/make.conf)
    proposal  - a set of changes proposed by the updated package
                this is the equivalent to the ._cfgXXXX_xyz.conf files
    change    - a continuos part of the proposal that differs from the
                currently used configuration file."""
        print self.help_quickstart.__doc__

    # current change state
    def assure_on_change(self):
        if self.current_change == None:
            raise NotOnChangeException

    def get_current_proposal_changes(self):
        self.assure_on_change()
        return self.current_change.proposal.get_changes()

    def get_current_file_changes(self):
        self.assure_on_change()
        filepath = self.current_change.proposal.get_file_path()
        return self.proposals.get_file_changes(filepath) 

    def get_current_dir_changes(self):
        self.assure_on_change()
        dirpath = os.path.dirname(self.current_change.get_file_path())
        return self.proposals.get_dir_changes(dirpath)

    def next_change(self):
        try:
            self.current_change = self.change_iter.next()
            while self.current_change.touched:
                self.current_change = self.change_iter.next()
        except StopIteration:
            self.cmdline.reached_end_of_changelist()

    def reached_end_of_changelist(self):
        self.current_change = None
        self.change_iter = self.proposals.get_all_changes().__iter__()
        msg = ['*** You reached the end of the changelist.',
            '*** You might want to check your changes with the list command.',
            '*** If you are satisfied, type "apply".']
        print self.colorizer.colorize('green', '\n'.join(msg))

    def update_prompt(self):
        if self.current_change is None:
            self.prompt = 'etc-proposals> '
        else:
            self.prompt = '%s> ' % self.current_change.get_id()

    # helpers
    def hop_on_and_show(self, args):
        if args.strip() in ['', 'change', 'file', 'dir']:   
            self.next_change()
            self.update_prompt()
        try:
            self.show_change()
        except NotOnChangeException:
            pass

def run_frontend():
    etc_cli = EtcProposalsCmdLine()
    etc_cli.cmdloop()

if __name__ == '__main__':
    run_frontend()
