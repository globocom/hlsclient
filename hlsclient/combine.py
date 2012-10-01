from copy import copy
import os

import m3u8

def combine_playlists(playlists, path):
    'Generate all neeed variant m3u8s and save them in disk'
    playlists_data = get_playlists_data(playlists)
    for action in get_actions(playlists, 'combine'):
        dump_variant_playlist(playlists_data, action, path)

def get_playlists_data(playlists):
    '''Creates a dict of playlists with their data.
    Valid playlists are those that we are consuming and
    those that we are creating by transcode.'''
    data = copy(playlists['streams'])
    for action in get_actions(playlists, 'transcode'):
        for output_type in ['audio', 'video']:
            data.update(action['output'].get(output_type, {}))
    return data

def get_actions(playlists, action_type):
    'Return only the combine actions from a given type'
    actions = playlists.get('actions', {})
    return [action for action in actions if action['type'] == action_type]

def dump_variant_playlist(playlists_data, action, path):
    'Saves variant m3u8 to file'
    m3u8 = generate_variant_playlist(playlists_data, action)
    m3u8.dump(path + action['output'])

def generate_variant_playlist(playlists_data, action):
    'Generate variant m3u8 in memory'
    variant_m3u8 = m3u8.M3U8()
    for playlist_name in action['input']:
        playlist = generate_single_playlist(playlists_data[playlist_name])
        variant_m3u8.add_playlist(playlist)
    return variant_m3u8

def generate_single_playlist(playlist_data):
    'Generate single m3u8 in memory'
    bandwidth = str(playlist_data['bandwidth'])
    m3u8_uri = playlist_data.get('input-path') or playlist_data.get('path')
    return m3u8.Playlist(m3u8_uri, stream_info={'bandwidth': bandwidth, 'program_id': '1'}, baseuri="")
