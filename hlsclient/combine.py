import os

import m3u8

def combine_playlists(playlists, path):
    streams = playlists['streams']
    for action in combine_actions(playlists):
        dump_variant_playlist(playlists, action, path)

def combine_actions(playlists):
    actions = playlists.get('actions', {})
    return [action for action in actions if action['type'] == 'combine']

def dump_variant_playlist(playlists, action, path):
    m3u8 = generate_variant_playlist(playlists, action)
    m3u8.dump(path + action['output'])

def generate_variant_playlist(playlists, action):
    variant_m3u8 = m3u8.M3U8()
    for playlist_name in action['input']:
        playlist = generate_single_playlist(playlists, playlist_name)
        variant_m3u8.add_playlist(playlist)
    return variant_m3u8

def generate_single_playlist(playlists, playlist_name):
    playlist_data = playlists['streams'][playlist_name]
    bandwidth = str(playlist_data['bandwidth'])
    m3u8_uri = playlist_data['input-path']
    return m3u8.Playlist(m3u8_uri, stream_info={'bandwidth': bandwidth, 'program_id': '1'}, baseuri="")
