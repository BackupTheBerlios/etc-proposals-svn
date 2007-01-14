#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a tool to integrate modified configs, post-emerge

__author__ = 'Björn Michaelsen' 
__version__ = '0.91.20070103'
__date__ = '2007-01-03'

import ConfigParser, anydbm, shelve, difflib, os, os.path, portage, re, shutil

STATEFILE = '/var/lib/etcproposals.state'

class OpcodeMismatchException(Exception):
    "happens when a state file is loaded, that does not match the proposal"
    pass

class FrontendFailedException(Exception):
    "happens when a Frontend fails to start"
    pass

class EtcProposalChange(object):
    def __init__(self, opcode, proposal):
        (self.opcode, self.proposal, self.merge, self.touched) = (opcode, proposal, False, (opcode[0] == 'equal'))

    def __getstate__(self):
        return (self.opcode, self.merge, self.touched)

    def __setstate__(self, state):
        (self.opcode, self.merge, self.touched) = state
    
    def copystatefrom(self, other):
        if not self.opcode == other.opcode:
            raise OpcodeMismatchException
        (self.touched, self.merge) = (other.touched, other.merge)

    def use(self):
        "include these changes into the new file"
        (self.touched, self.merge) = (True, True)
        self.on_changed()

    def zap(self):
        "dont include these changes into the new file"
        (self.touched, self.merge) = (True, False)
        self.on_changed()

    def undo(self):
        "reset use/zap decision for this change"
        (self.touched, self.merge) = ((self.opcode[0] == 'equal'), False)
        self.on_changed()

    def get_file_path(self):
        "path to the config file, which this change proposes to change"
        return self.proposal.get_file_path()

    def get_proposal_path(self):
        "path to the proposal, where this change resides"
        return self.proposal.get_proposal_path()

    def get_revision(self):
        "the number in the ._cfgXXXX_ part of a proposals filename"
        return self.proposal.get_revision()

    def get_base_content(self):
        "the current (old) file content"
        return self.proposal.get_base_lines(self.opcode)

    def get_proposed_content(self):
        "the proposed (new) file content"
        return self.proposal.get_proposed_lines(self.opcode)

    def get_filepart_content(self):
        "the file content, as it would be merged with the current zap/use decision"
        if self.merge:
            return self.get_proposed_content()
        return self.get_base_content()

    def is_nullchange(self):
        "True, if the change describes a unchanged filepart"
        return (self.opcode[0] == 'equal')

    def is_whitespace_only(self):
        "True, if the change only modifies whitespace file content"
        return self._contains_only_matching_lines('^\s*$')

    def is_cvsheader(self):
        "True, if the change only modifies a CVS header"
        return self._contains_only_matching_lines('^# .Header:.*$')
    
    def on_changed(self):
        "Event, should be fired, if the change changes ;-)"
        self.proposal.on_changed()

    def _contains_only_matching_lines(self, regexpstring):
        regexp = re.compile(regexpstring)
        for line in self.get_base_content() + self.get_proposed_content():
            if not regexp.match(line):
                return False
        return True


class EtcProposal(object):
    def __init__(self, path, proposals):
        (self.path, self.proposals) = (os.path.abspath(path), proposals)
        (self.base_lines, self._changes) = (None, None)

    def __cmp__(self, other):
        pathcmp = cmp(os.path.dirname(self.path), os.path.dirname(other.path))
        if pathcmp:
            return pathcmp
        filenamecmp = cmp(self.get_file_path(), other.get_file_path())
        if filenamecmp:
            return filenamecmp
        return cmp(self.get_revision(), other.get_revision())

    def apply(self):
        "merges all decisions for this proposal (and those with lower revisions)"
        file_path = self.get_file_path()
        merged_configpath = file_path + '.merged'
        bak_configpath = file_path + '.bak'
        fd = open(merged_configpath, 'w')
        fd.writelines(self.get_merged_content())
        fd.close()
        try:
            shutil.copymode(file_path, merged_configpath)
            shutil.copystat(file_path, merged_configpath)
            shutil.move(file_path, bak_configpath)
        except OSError:
            pass
        shutil.move(merged_configpath, file_path)
        try:
            os.unlink(file_path + '.bak')
        except OSError:
            pass
        self.base_lines = None
        self._changes = None
        try:
            os.unlink(self.path)
        except OSError:
            pass
        del EtcProposalsState()[self._get_state_url()]

    def clear_cache(self):
        "clears all state data"
        self.on_changed()
        self.base_lines = None
        self._changes = None

    def get_file_path(self):
        "path to the config file, which this proposal proposes to change"
        return os.path.join(
            os.path.dirname(self.path),
            EtcProposal.proposal_regexp().match(os.path.basename(self.path)).groups()[0]) 

    def get_proposal_path(self):
        "path to the proposal"
        return self.path
    
    def get_revision(self):
        "the number in the ._cfgXXXX_ part of a proposals filename"
        return int(os.path.basename(self.path)[5:9])

    def get_base_content(self):
        "the current (old) file content"
        if self.base_lines is None:
            baseproposal = self.proposals.get_previous_proposal(self)
            if baseproposal is None:
                try:
                    self.base_lines = self._get_file_content(self.get_file_path())
                except IOError:
                    self.base_lines = []
            else:
                self.base_lines = baseproposal.get_merged_content()
        return self.base_lines

    def get_proposed_content(self):
        "the proposed (new) file content"
        return self._get_file_content(self.path)

    def get_merged_content(self):
        "the file content, as it would be merged with the current zap/use decisions"
        self._assure_changes_exists()
        filelines = list()
        [filelines.extend(change.get_filepart_content()) for change in self._changes]
        return filelines

    def get_changes(self):
        self._assure_changes_exists()
        return [change for change in self._changes if not change.is_nullchange()]

    def get_base_lines(self, opcode):
        return self.get_base_content()[opcode[1]:opcode[2]]

    def get_proposed_lines(self, opcode):
        return self.get_proposed_content()[opcode[3]:opcode[4]]

    def is_finished(self):
        "True, if all changes have been decided on"
        if self._changes is None:
            return False
        return reduce(lambda x,y: x and y, (change.touched for change in self._changes))

    def on_changed(self):
        "Event, should be fired, if the proposal changes"
        self._assure_changes_exists()
        undecorated_changes = list()
        for change in self._changes:
            undecorated_change = EtcProposalChange(change.opcode, None)
            undecorated_change.copystatefrom(change)
            undecorated_changes.append(undecorated_change)
        EtcProposalsState()[self._get_state_url()] = undecorated_changes    
        self.proposals.on_proposal_changed(self)

    def _assure_changes_exists(self):
        if self._changes is None:
            self._changes = [self._create_change(opcode) for opcode in self._get_opcodes()]
            state = EtcProposalsState()
            if state.has_key(self._get_state_url()):
                undecorated_changes = EtcProposalsState()[self._get_state_url()]
                try:
                    [change.copystatefrom(undecorated_changes.pop(0)) for change in self._changes]
                except OpcodeMismatchException:
                    pass
                except IndexError:
                    pass

    def _get_state_url(self):
        return 'changedecisions://' + os.path.join(self.path, '%4d' % self.get_revision())

    def _get_file_content(self, filepath):
        fd = open(filepath)
        content = fd.readlines()
        fd.close()
        return content

    def _get_opcodes(self):
        return difflib.SequenceMatcher(
            None,
            self.get_base_content(),
            self.get_proposed_content()).get_opcodes()

    def _create_change(self, opcode):
        return EtcProposalChange(opcode, self)

    # static
    @staticmethod
    def proposal_regexp():
        "identifies a proposal filename"
        return re.compile('^\._cfg[0-9]{4}_(.*)')

    # deprecated old style statefile
    @staticmethod
    def state_regexp():
        "identifies a proposal state filename"
        return re.compile('^\._cfgstate[0-9]{4}_(.*)')

class EtcProposals(list):
    def __init__(self):
        list.__init__(self)
        self.refresh()

    def refresh(self):
        "clears and repopulates the list from the filesystem"
        del self[:] 
        for dir in portage.settings['CONFIG_PROTECT'].split(' '):
            self._add_update_proposals(dir)
        self.sort()

    def clear_all_states(self):
        "this is pretty much 'undo all' but it also removes orphaned state files"
        # removing deprecated old style statefile
        for dir in portage.settings['CONFIG_PROTECT'].split(' '):
            self._remove_statefiles(dir)
        self.refresh()

    def apply(self):
        "merges all finished proposals"
        [proposal.apply() for proposal in self if proposal.is_finished()]
        self.refresh()

    def get_files(self):
        "returns a list of config files which have update proposals"
        configpaths = list(set((
            proposal.get_file_path() for proposal in self)))
        configpaths.sort()
        return configpaths

    def get_file_changes(self, file_path):
        "returns a list of changes for a config file"
        changes = list()
        for proposal in self.get_file_proposals(file_path):
            changes.extend(proposal.get_changes())
        return changes

    def get_file_proposals(self, file_path):
        "returns a list of proposals for a config file"
        return [proposal for proposal in self
            if proposal.get_file_path() == file_path]

    def get_dir_changes(self, dir_path):
        "returns a list of changes for config files in a directory"
        changes = list()
        for proposal in self:
            if proposal.get_file_path().startswith(dir_path):
                changes.extend(proposal.get_changes())
        return changes

    def get_all_changes(self):
        "returns a list all changes"
        return (change for proposal in self
            for change in proposal.get_changes())

    def get_whitespace_changes(self):
        "returns a list of changes only changing whitespaces"
        return [change for change in self.get_all_changes() if change.is_whitespace_only()]

    def get_cvsheader_changes(self):
        "returns a list of changes only changing CVS-Header"
        return [change for change in self.get_all_changes() if change.is_cvsheader()]

    def get_previous_proposal(self, proposal):
        "returns the previous revision for a config file"
        revision = proposal.get_revision()
        previous_proposal = None
        for p in self.get_file_proposals(proposal.get_file_path()):
            if p.get_revision() < revision:
                previous_proposal = p
        return previous_proposal

    def on_proposal_changed(self, proposal):
        "Event, should be fired, if a proposal changes"
        revision = proposal.get_revision()
        file_path = proposal.get_file_path()
        [p.clear_cache()
            for p in self.get_file_proposals(file_path)
            if p.get_revision() > revision]

    def _add_update_proposals(self, dir):
        up_regexp = EtcProposal.proposal_regexp()
        self.extend(( self._create_proposal(os.path.join(path, file)) 
            for (path, dirs, files) in os.walk(dir) for file in files
            if up_regexp.match(file) ))

    # removing deprecated old style statefile
    def _remove_statefiles(self, dir):
        state_regexp = EtcProposal.state_regexp()
        [os.unlink(os.path.join(path, file)) 
            for (path, dirs, files) in os.walk(dir) for file in files
            if state_regexp.match(file)]

    def _create_proposal(self, proposal_path):
        return EtcProposal(proposal_path, self)

class EtcProposalsConfig(object):
    def __init__(self):
        configlocations = ['.', '/etc']
        self.parser = ConfigParser.ConfigParser()
        self.parser.read([os.path.join(configlocation, 'etc-proposals.conf')
            for configlocation in configlocations])

    def PreferedFrontends(self):
        try:
            return self.parser.get('General', 'PreferedFrontends').split(';')
        except Exception, e:
            print e
            return []

    def StartupCommands(self):
        try:
            return self.parser.get('General', 'StartupCommands').split(';')
        except Exception:
            return []

class EtcProposalsState(shelve.Shelf):
    def __init__(self):
        shelve.Shelf.__init__(self, anydbm.open(STATEFILE, 'c'))

__all__ = ['EtcProposalChange', 'EtcProposal', 'EtcProposals', 'EtcProposalsConfig']

if __name__ == '__main__':
    raise SystemExit, 'This module is not executable.' 
