
import shlex, string
import pprint


def portage_utils_getconfig(mycfg):
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

def get_config_protect():
	local_settings =  portage_utils_getconfig('make.conf')
	global_settings = portage_utils_getconfig('/etc/make.globals')
	config_protect = ''
	if global_settings.has_key('CONFIG_PROTECT'):
		config_protect = global_settings['CONFIG_PROTECT'][1:-1]
	if local_settings.has_key('CONFIG_PROTECT'):
		config_protect = config_protect + ' ' + local_settings['CONFIG_PROTECT'][1:-1]
	return config_protect.split()
	
pprint.pprint(get_config_protect())
