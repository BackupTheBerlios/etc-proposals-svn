#! /usr/bin/python
import portage_stubs, pprint

files = set(['/etc/make.conf', '/etc/mplayer.conf', '/etc/host.conf', '/etc/irssi.conf', '/etc/gtk/gtkrc.az', 'dsfdsdfs'])
pprint.pprint(portage_stubs.PortageInterface.get_md5_from_vdb(files))
