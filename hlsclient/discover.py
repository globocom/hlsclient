import os
import json
import logging
import urllib
import urlparse
from collections import namedtuple

import m3u8

Server = namedtuple('Server', 'server port')

def discover_playlist_paths_and_create_indexes(config, destination):
    playlists = discover(config)
    _create_index_for_variant_playlists(playlists, destination)
    paths = _get_paths(playlists)
    logging.info(u'Discovered the following paths: %s' % paths.items())
    return paths

def discover_playlists(config):
    '''
    Get dictionary returned by discover and converts to a dictionary with format:
    {
        '/h100.m3u8': {
            [Server('http://server1'), Server('http://server3')],
        },
        '/h200.m3u8': {
            [Server('http://server2'), Server('http://server3')],
        },
        '/playlist_without_mbr.m3u8': {
            [Server('http://server1'), Server('http://server2')],
        }
    }

    '''
    playlists = discover(config)
    return _get_paths(playlists)

def _get_paths(playlists):
    paths = {}
    for main_m3u8_uri, playlist_info in playlists.items():
        for m3u8_uri, playlist_info in playlist_info['streams'].items():
            paths[m3u8_uri] = playlist_info['servers']
    return paths

def discover(config):
    '''
    Discover available playlists from URL in config and parses into dictionary
    suitable for internal usage.

    URL is expected to have the format below.

    {'actives': [{
        'm3u8': playlist_with_mbr.m3u8',
        'servers': []
        'bitrates': [
            {
                'm3u8': '/h100.m3u8',
                'servers': ['http://server1', 'http://server3'],
                'bandwidth': '10000'
            },
            {
                'm3u8': '/h200.m3u8'
                'servers': ['http://server2', 'http://server3'],
                'bandwidth': '20000'
            }
        ],
        'needs_index': True,
    },
    {
        'm3u8': 'playlist_without_mbr.m3u8',
        'servers': ['http://server1', 'http://server2'],
        'bitrates': []
        'needs_index': False,
    }]}
    '''
    api_url = config.get('discover', 'api_url')
    playlists = {}

    for playlist_info in _get_streams_from_url(api_url):
        m3u8_uri = playlist_info['m3u8']
        streams = {}
        playlists[m3u8_uri] = {'needs_index': playlist_info['needs_index'], 'streams': streams}

        if playlist_info['needs_index']:
            _append_m3u8_with_mbr_to(streams, playlist_info)
        else:
            _append_m3u8_without_mbr_to(streams, playlist_info)

    return playlists

def _get_streams_from_url(url):
    # FIXME: implement error checking
    return json.load(urllib.urlopen(url))['actives']

def _create_index_for_variant_playlists(playlists, destination):
    for m3u8_uri, playlist_info in playlists.items():
        if playlist_info['needs_index']:
            _generate_variant_playlist(playlist_info, destination + m3u8_uri)

def _generate_variant_playlist(playlist_info, destination):
    variant_m3u8 = m3u8.M3U8()
    for m3u8_uri in playlist_info['streams']:
        bandwidth = _get_bandwidth(playlist_info, m3u8_uri)
        playlist = m3u8.Playlist(m3u8_uri, stream_info={'bandwidth': bandwidth, 'program_id': '1'}, baseuri="")
        variant_m3u8.add_playlist(playlist)
    variant_m3u8.dump(destination)

def _get_bandwidth(playlist_info, m3u8_uri):
    return str(playlist_info['streams'][m3u8_uri]['bandwidth'])

def _append_m3u8_without_mbr_to(result, playlist_info):
    playlist = playlist_info['m3u8']
    result[playlist] = {'servers': _build_servers(playlist_info['servers'])}

def _append_m3u8_with_mbr_to(result, playlist_info):
    bitrates = playlist_info['bitrates']
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
