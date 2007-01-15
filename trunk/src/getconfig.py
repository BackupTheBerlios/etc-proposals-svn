
import pprint

try:
    raise ImportError
    import portage
    class PortageInterface(object):
        @staticmethod 
        def get_config_protect():
            return portage.settings['CONFIG_PROTECT'].split(' ')

except ImportError:
    from portage_stubs import PortageInterface

pprint.pprint(PortageInterface.get_config_protect())
print PortageInterface.colorize('red', 'red')
print PortageInterface.colorize('green', 'green')
print PortageInterface.colorize('white', 'white')
print PortageInterface.colorize('red', 'red')

