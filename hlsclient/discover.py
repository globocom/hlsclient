import os
import json
import urllib
import urlparse
from collections import namedtuple

import m3u8

Server = namedtuple('Server', 'server port')

class PlaylistDiscover(object):
    def __init__(self, config):
        self.playlists = discover(config)
        self.playlist_paths = self.get_paths(self.playlists)

    def get_paths(self, playlists):
        paths = {}
        for m3u8_uri, info in playlists.items():
            paths.update(self._get_servers(info['streams']))

        return paths

    def create_index_for_variant_playlists(self, destination):
        for m3u8_uri, info in self.playlists.items():
            if info['needs_index']:
                self._generate_variant_playlist(info, destination + m3u8_uri)

    def _generate_variant_playlist(self, info, destination):
        variant_m3u8 = m3u8.M3U8()
        for m3u8_uri in info['streams']:
            bandwidth = self._get_bandwidth(info, m3u8_uri)
            playlist = m3u8.Playlist(m3u8_uri, stream_info={'bandwidth': bandwidth, 'program_id': '1'}, baseuri="")
            variant_m3u8.add_playlist(playlist)

        variant_m3u8.dump(destination)

    def _get_bandwidth(self, info, m3u8_uri):
        return str(info['streams'][m3u8_uri]['bandwidth'])

    def _get_servers(self, streams):
        result = {}
        for m3u8_uri, info in streams.items():
            result[m3u8_uri] = info['servers']

        return result

def discover(config):
    '''
    Returns a dictionary with format:

    {
        'playlist_with_mbr.m3u8': {
            'streams': {
                'h100.m3u8': {
                    'servers': [Server('http://server1'), Server('http://server3')],
                    'bandwidth': '10000'
                },
                'h200.m3u8': {
                    'servers': [Server('http://server2'), Server('http://server3')],
                    'bandwidth': '10000'
                }
            },
            'needs_index': True,
        },

        'playlist_without_m3u8.m3u8':{
            'streams': {
                'playlist_without_m3u8.m3u8': {
                    'servers': [Server('http://server1'), Server('http://server2')],
                    'bandwidth': '1000000'
                }
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

        if info['needs_index']:
            _append_m3u8_with_mbr_to(streams, info)
        else:
            _append_m3u8_without_mbr_to(streams, info)

    return playlists


def get_info_from_url(url):
    # FIXME: implement error checking
    return json.load(urllib.urlopen(url))['actives']

def _append_m3u8_without_mbr_to(result, info):
    playlist = info['m3u8']
    result[playlist]['servers'] = _build_servers(info['servers'])

def _append_m3u8_with_mbr_to(result, info):
    bitrates = info['bitrates']
    for m3u8 in bitrates:
        playlist = m3u8['m3u8']
        result[playlist] = {}
        result[playlist]['servers'] = _build_servers(m3u8['servers'])
        result[playlist]['bandwidth'] = m3u8['bandwidth']

def _build_servers(servers):
    result = []
    for server in servers:
        parsed_url = urlparse.urlparse(server)
        server_url = '{scheme}://{hostname}'.format(scheme=parsed_url.scheme, hostname=parsed_url.hostname)
        port = parsed_url.port or 80
        result.append(Server(server=server_url, port=port))
    return result
