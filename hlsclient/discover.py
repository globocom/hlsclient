import json
import urllib
from collections import namedtuple


Server = namedtuple('Server', 'server port')


def discover(config):
    '''
    Receives the extra configuration parameters from [discover] section

    Returns a dictionary with format:

      {'/path1.m3u8': ['server1', 'server2'],
       '/path2.m3u8': ['server3', 'server4', 'server5']}

    '''
    api_url = config.get('discover', 'api_url')
    result = {}
    info = get_info_from_url(api_url)
    for info in get_info_from_url(api_url):
        m3u8 = info['m3u8']
        servers = [Server(server=server, port=80) for server in info['servers']]
        result[m3u8] = servers
    return result


def get_info_from_url(url):
    # FIXME: implement error checking
    return json.load(urllib.urlopen(url))['actives']