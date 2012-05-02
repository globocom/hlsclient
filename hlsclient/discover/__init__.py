import importlib

def discover(config):
    '''
    Receives the extra configuration parameters from [discover] section

    Returns a dictionary with format:

      {'/path1.m3u8': ['server1', 'server2'],
       '/path2.m3u8': ['server3', 'server4', 'server5']}

    '''
    module_name = config.get('discover', 'backend')
    print module_name
    discover_module = importlib.import_module(module_name)
    return discover_module.discover(config)
