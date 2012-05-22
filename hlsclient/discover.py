import json
import urllib
import urlparse
from collections import namedtuple


Server = namedtuple('Server', 'server port')

class PlaylistDiscover(object):
    def __init__(self, config):
        self.playlists = discover(config)
        self.playlist_paths = self.get_paths(self.playlists)

    def get_paths(self, playlists):
        paths = {}
        for m3u8_uri, info in playlists.items():
            paths.update(info['streams'])

        return paths

def discover(config):
    '''
    Returns a dictionary with format:

    {
        'playlist_with_mbr.m3u8': {
            'streams': {
                'h100.m3u8': [Server('http://server1'), Server('http://server3')],
                'h200.m3u8': [Server('http://server2'), Server('http://server3')],
            },
            'needs_index': True,
        },

        'playlist_without_m3u8.m3u8':{
            'streams': {
                'playlist_without_m3u8.m3u8': [Server('http://server1'), Server('http://server2')],
            },
            'needs_index': False,
        }
    }

    '''
    api_url = config.get('discover', 'api_url')
    info = get_info_from_url(api_url)
    playlists = {}

    for info in get_info_from_url(api_url):
        m3u8_uri = info['m3u8']
        streams = {}
        playlists[m3u8_uri] = {'needs_index': info['needs_index'], 'streams': streams}

        if not info['needs_index']:
            _append_m3u8_without_mbr_to(streams, info)
        else:
            _append_m3u8_with_mbr_to(streams, info)

    return playlists


def get_info_from_url(url):
    # FIXME: implement error checking
    return json.load(urllib.urlopen(url))['actives']

def _append_m3u8_without_mbr_to(result, info):
    playlist = info['m3u8']
    result[playlist] = _build_servers(info['servers'])


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
        port = parsed_url.port or 80
        result.append(Server(server=server_url, port=port))
    return result
