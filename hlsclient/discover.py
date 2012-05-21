import json
import urllib
import urlparse
from collections import namedtuple


Server = namedtuple('Server', 'server port')


def discover(config):
    '''
    Returns a dictionary with format:

      {'/playlist1.m3u8': [Server('server1'), Server('server2')],
       '/playlist2.m3u8': [Server('server2'), Server('server3'), Server('server4')]}

    '''
    api_url = config.get('discover', 'api_url')
    result = {}
    for info in get_info_from_url(api_url):
        if not info['needs_index']:
            _append_m3u8_without_mbr_to(result, info)
        else:
            _append_m3u8_with_mbr_to(result, info)
    return result


def get_info_from_url(url):
    # FIXME: implement error checking
    return json.load(urllib.urlopen(url))['actives']

def _append_m3u8_without_mbr_to(result, info):
    playlist = info['m3u8']
    result[playlist] = _build_servers(m3u8['servers'])


def _append_m3u8_with_mbr_to(result, info):
    bitrates = info['bitrates']
    for m3u8 in bitrates:
        playlist = m3u8['m3u8']
        result[playlist] = _build_servers(m3u8['servers'])

def _build_servers(servers):
    result = []
    for server in servers:
        parsed_url = urlparse.urlparse(server)
        server_url = '{scheme}://{hostname}'.format(scheme=parsed_url.scheme, hostname=parsed_url.hostname)
        port = parsed_url.port
        result.append(Server(server=server_url, port=port))
    return result