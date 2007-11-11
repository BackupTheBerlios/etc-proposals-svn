#!/usr/bin/env python
#! -*- coding: utf-8 -*-
# Copyright 2006, 2007 Björn Michaelsen
# Distributed under the terms of the GNU General Public License v2

# etc-proposals - a tool to integrate modified configs, post-emerge

__author__ = 'Björn Michaelsen' 
__version__ = '1.4'
__date__ = '2007-10-08'

import ConfigParser, anydbm, shelve, difflib, os, os.path, re, shutil, md5
from etcproposals.portage_stubs import PortageInterface
    
STATEFILE = '/var/state/etcproposals.state'


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

    def __setstate__(self, new_state):
        (self.opcode, self.merge, self.touched) = new_state
    
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

    def get_action(self):
        "Returns the the proposed action of this change. One of ['insert', 'delete', 'replace']."
        return self.opcode[0]
    
    def get_affected_lines(self):
        "Returns a tuple (startline, endline) describing the affected lines."
        return (self.opcode[1]+1, self.opcode[2]+1)

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

    def get_status(self):
        "returns the status of the change (undecided/use/zap)"
        if not self.touched:
            return 'undecided'
        elif self.merge:
            return 'use'
        return 'zap'

    def is_nullchange(self):
        "True, if the change describes a unchanged filepart"
        return (self.opcode[0] == 'equal')

    def is_whitespace_only(self):
        "True, if the change only modifies whitespace file content"
        if self.proposal.proposals._whitespace_changes != None:
            return self in self.proposal.proposals._whitespace_changes
        return self._contains_only_matching_lines('^\s*$')

    def is_cvsheader(self):
        "True, if the change only modifies a CVS header"
        if self.proposal.proposals._cvsheader_changes != None:
            return self in self.proposal.proposals._cvsheader_changes
        return self._contains_only_matching_lines('^# .Header:.*$')

    def is_unmodified(self):
        "True, if the change should change a config file, which has not been changed (its the same as the one provided with the package"
        if self.proposal.proposals._unmodified_changes != None:
            return self in self.proposal.proposals._unmodified_changes
        return EtcProposalConfigFile(self.proposal.get_file_path()).is_unmodified()
    
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
        self.clear_state()
    
    def clear_state(self):
        if State.has_key(self._get_state_url()):
            del State[self._get_state_url()]

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
        self._refresh_changes_cache()
        filelines = list()
        [filelines.extend(change.get_filepart_content()) for change in self._changes]
        return filelines

    def get_changes(self):
        self._refresh_changes_cache()
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
        self._refresh_changes_cache()
        undecorated_changes = list()
        for change in self._changes:
            undecorated_change = EtcProposalChange(change.opcode, None)
            undecorated_change.copystatefrom(change)
            undecorated_changes.append(undecorated_change)
        State[self._get_state_url()] = undecorated_changes    
        self.proposals.on_proposal_changed(self)

    def _refresh_changes_cache(self):
        if self._changes is None:
            opcodes = self._get_opcodes()
            if len(opcodes) > Config.MaxChangesPerProposal():
                opcodes = [self._join_opcodes(opcodes)]
            self._changes = [self._create_change(opcode) for opcode in opcodes]
            if State.has_key(self._get_state_url()):
                try:
                    undecorated_changes = State[self._get_state_url()]
                    [change.copystatefrom(undecorated_changes.pop(0)) for change in self._changes]
                except Exception:
                    pass

    def _join_opcodes(self, opcodes):
        return (
            'replace',
            reduce(min, (opcode[1] for opcode in opcodes)),
            reduce(max, (opcode[2] for opcode in opcodes)),
            reduce(min, (opcode[3] for opcode in opcodes)),
            reduce(max, (opcode[4] for opcode in opcodes)))

    def _get_state_url(self):
        return 'EtcProposal://' + self.path

    def _get_file_content(self, filepath):
        return FileCache.readlines_from_file(filepath)

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


class EtcProposalConfigFile(object):
    def __init__(self, path):
        self.path = path

    def md5hexdigest(self):
        "calculates the md5sum of the file in the fs"
        return md5.md5(open(self.path).read()).hexdigest()
    
    def is_unmodified(self):
        "True, if the file in the fs has the same md5 as recorded"
        if not State.has_key(self._get_state_url()):
            return False
        try:
            return (State[self._get_state_url()] == self.md5hexdigest())
        except IOError:
            return False

    def clear_unmodified(self):
        "clears the memory about this config file"
        if State.has_key(self._get_state_url()):
            del State[self._get_state_url()]

    def update_unmodified(self, expected_md5):
        "records the md5 if it matches the one of the file in the fs"
        if expected_md5 == self.md5hexdigest():
            State[self._get_state_url()] = expected_md5 
        else:
            self.clear_unmodified()

    def _get_state_url(self):
        return 'EtcProposalConfigFile://' + self.path


class EtcProposals(list):
    def __init__(self, refresh_on_init=True):
        list.__init__(self)
        self.clear_cache()
        if refresh_on_init:
            self.refresh()

    def refresh(self, current_file_callback = None):
        "clears and repopulates the list from the filesystem"
        self.clear_cache()
        del self[:] 
        for dir in PortageInterface.get_config_protect(Config.Backend()):
            self._add_update_proposals(dir, current_file_callback)
        self.sort()

    def clear_all_states(self):
        "this is pretty much 'undo all' but it also removes orphaned state files"
        State.clear_orphaned(self)
        self.refresh()

    def clear_cache(self):
        self._changes = None
        self._whitespace_changes = None
        self._cvsheader_changes = None
        self._unmodified_changes = None
        self._used_changes = None
        self._zapped_changes = None
        self._undecided_changes = None
        
    def apply(self, update_unmodified = False, current_file_callback = None):
        "merges all finished proposals"
        finished_proposals = [proposal for proposal in self if proposal.is_finished()]
        for proposal in finished_proposals:        
            if not current_file_callback is None: current_file_callback(proposal.get_file_path())
            proposal.apply()
        if update_unmodified:
            self.update_unmodified(finished_proposals)
        self.clear_orphaned_proposals()
        self.clear_orphaned_configfiles()
        self.refresh()

    def get_files(self):
        "returns a list of config files which have update proposals"
        configpaths = list(set((
            proposal.get_file_path() for proposal in self)))
        configpaths.sort()
        return configpaths
    
    def update_unmodified(self, finished_proposals):
        "records the md5 if it matches the one of the file in the fs"
        finished_filepaths = set((proposal.get_file_path() for proposal in finished_proposals))
        expected_md5s =  PortageInterface.get_md5_from_vdb(finished_filepaths)
        for (path, expected_md5) in expected_md5s.iteritems():
            EtcProposalConfigFile(path).update_unmodified(expected_md5)
        for path in (finished_filepaths - set(expected_md5s.keys())):
            EtcProposalConfigFile(path).clear_unmodified()

    def get_file_changes(self, file_path):
        "returns a list of changes for a config file"
        return list(self.get_file_changes_gen(file_path))

    def get_file_changes_gen(self, file_path):
        "returns a generator of changes for a config file (get a new generator, if you modify changes)"
        return (change for proposal in self.get_file_proposals(file_path)
            for change in proposal.get_changes())

    def get_file_proposals(self, file_path):
        "returns a list of proposals for a config file"
        return [proposal for proposal in self
            if proposal.get_file_path() == file_path]

    def get_dir_changes(self, dir_path):
        "returns a list of changes for config files in a directory"
        return list(self.get_dir_changes_gen(dir_path))

    def get_dir_changes_gen(self, dir_path):
        "returns a generator of changes for config files in a directory (get a new generator, if you modify changes)"
        matching_proposals = [proposal for proposal in self
            if proposal.get_file_path().startswith(dir_path)]
        return (change for proposal in matching_proposals 
            for change in proposal.get_changes())

    def get_all_changes(self):
        "returns a list all changes"
        self._refresh_changes_cache()
        return self._changes

    def get_whitespace_changes(self):
        "returns a list of changes only changing whitespaces"
        self._refresh_whitespace_changes_cache()
        return self._whitespace_changes

    def get_cvsheader_changes(self):
        "returns a list of changes only changing CVS-Header"
        self._refresh_cvsheader_changes_cache()
        return self._cvsheader_changes
    
    def get_unmodified_changes(self):
        "returns a list of changes of unmodified files"
        self._refresh_unmodified_changes_cache()
        return self._unmodified_changes

    def get_used_changes(self):
        "returns a list of used changes"
        self._refresh_used_changes_cache()
        return self._used_changes

    def get_zapped_changes(self):
        "returns a list of zapped changes"
        self._refresh_zapped_changes_cache()
        return self._zapped_changes

    def get_undecided_changes(self):
        "returns a list of undecided changes"
        self._refresh_undecided_changes_cache()
        return self._undecided_changes

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
        self.clear_cache()
        revision = proposal.get_revision()
        file_path = proposal.get_file_path()
        [p.clear_cache()
            for p in self.get_file_proposals(file_path)
            if p.get_revision() > revision]

    def _add_update_proposals(self, dir, current_file_callback):
        up_regexp = EtcProposal.proposal_regexp()
        self.extend((
            self._create_proposal(os.path.join(path, file), current_file_callback)
            for (path, dirs, files) in os.walk(dir) for file in files
            if up_regexp.match(file) ))

    def _create_proposal(self, proposal_path, current_file_callback):
        if not current_file_callback is None: current_file_callback(proposal_path)
        return EtcProposal(proposal_path, self)
    
    def _refresh_changes_cache(self):
        if self._changes == None:
            self._changes = [change for proposal in self for change in proposal.get_changes()]

    def _refresh_whitespace_changes_cache(self):
        if self._whitespace_changes == None:
            self._whitespace_changes = [change for change in self.get_all_changes() if change.is_whitespace_only()]
    
    def _refresh_cvsheader_changes_cache(self):
        if self._cvsheader_changes == None:
            self._cvsheader_changes = [change for change in self.get_all_changes() if change.is_cvsheader()]

    def _refresh_unmodified_changes_cache(self):
        if self._unmodified_changes == None:
            self._unmodified_changes = [change for change in self.get_all_changes() if change.is_unmodified()]

    def _refresh_used_changes_cache(self):
        if self._used_changes == None:
            self._used_changes = [change for change in self.get_all_changes() if change.get_status() == 'use']

    def _refresh_zapped_changes_cache(self):
        if self._zapped_changes == None:
            self._zapped_changes = [change for change in self.get_all_changes() if change.get_status() == 'zap']

    def _refresh_undecided_changes_cache(self):
        if self._undecided_changes == None:
            self._undecided_changes = [change for change in self.get_all_changes() if change.get_status() == 'undecided']

    @staticmethod
    def scan_all_files():
        allpkgparts = PortageInterface.get_fileinfo_from_vdb(
            [os.path.join(path, file)
            for configbasedir in PortageInterface.get_config_protect(
                Config.Backend())
            for (path, dir, files) in os.walk(configbasedir)
            for file in files])
        return len([EtcProposalConfigFile(pkgpart.path).update_unmodified(pkgpart.md5) for pkgpart in allpkgparts.values()])


class EtcProposalFileCache(object):
    def __init__(self, max_cached_files):
        self.max_cached_files = max_cached_files
        self.clear()

    def readlines_from_file(self, filepath):
        self._add_cached_file(filepath)
        return self.cached_content[filepath]

    def _add_cached_file(self, filepath):
        if filepath in self.last_files:
            self.last_files.remove(filepath)
        self.last_files.append(filepath)
        if len(self.last_files) > self.max_cached_files:
            del self.cached_content[self.last_files.pop(0)]
        if filepath not in self.cached_content:
            self.cached_content[filepath] = open(filepath).readlines()

    def clear(self):
        self.last_files = list()
        self.cached_content = dict()
        

class EtcProposalsConfig(object):
    fastexit_override = None
    prefered_frontends_override = None

    def __init__(self):
        configlocations = ['.', '/etc']
        self.parser = ConfigParser.ConfigParser()
        self.parser.read([os.path.join(configlocation, 'etc-proposals.conf')
            for configlocation in configlocations])

    def PreferedFrontends(self):
        try:
            if EtcProposalsConfig.prefered_frontends_override != None:
                return EtcProposalsConfig.prefered_frontends_override
            else:
                return self.parser.get('General', 'PreferedFrontends').split(',')
        except Exception, e:
            return []
    
    def Backend(self):
        try:
            return self.parser.get('General', 'Backend')
        except Exception, e:
            return 'portage'

    def Fastexit(self):
        try:
            if EtcProposalsConfig.fastexit_override != None:
                return EtcProposalsConfig.fastexit_override
            else:
                return (self.parser.get('General', 'Fastexit') == 'True')
        except Exception, e:
            return False
    
    def MaxCachedFiles(self):
        try:
            return self.parser.getint('General', 'MaxCachedFiles')
        except Exception, e:
            return 10

    def MaxChangesPerProposal(self):
        try:
            return self.parser.getint('General', 'MaxChangesPerProposal')
        except Exception, e:
            return 100

    @staticmethod
    def FastexitOverride(override_value):
        EtcProposalsConfig.fastexit_override = override_value
    
    @staticmethod
    def PreferedFrontendsOverride(override_value):
        EtcProposalsConfig.prefered_frontends_override = override_value
        

class EtcProposalsState(shelve.Shelf):
    def __init__(self):
        shelve.Shelf.__init__(self, anydbm.open(STATEFILE, 'c'))
    
    def get_configfiles(self):
        return (key for key in self.keys() if key.startswith('EtcProposalConfigFile:'))

    def get_proposals(self):
        return (key for key in self.keys() if key.startswith('EtcProposal:'))

    def clear_orphaned(self, current_proposals):
        self.clear_orphaned_configfiles()
        self.clear_orphaned_proposals(current_proposals)
    
    def clear_orphaned_proposals(self, current_proposals):
        stateproposalsfiles = set(self.get_proposals())
        fsproposalsfiles = set(current_proposals)
        for proposal in (stateproposalsfiles-fsproposalsfiles):
            del self[proposal]
    
    def clear_orphaned_configfiles(self):
        for stateconfigfile in self.get_configfiles():
            if not os.path.exists(stateconfigfile.replace('EtcProposalConfigFile://','',1)):
                del self[stateconfigfile]
    
    def clear_all(self):
        for key in self.keys():
            del self[key]
        

__all__ = ['EtcProposalChange', 'EtcProposal', 'EtcProposals', 'EtcProposalsConfig', 'FrontendFailedException']

if __name__ == '__main__':
    raise SystemExit, 'This module is not executable.' 


# Singletons

Config = EtcProposalsConfig()
FileCache = EtcProposalFileCache(Config.MaxCachedFiles())
State = EtcProposalsState()
