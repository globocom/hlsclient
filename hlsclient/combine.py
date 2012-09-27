import os

import m3u8

def combine_playlists(playlists, path):
    streams = playlists['streams']
    actions = playlists.get('actions', {})
    combine_actions = [action for action in actions if action['type'] == 'combine']
    for action in combine_actions:
        generate_variant_playlist(action, playlists, path)

def generate_variant_playlist(action, playlists, path):
    variant_m3u8 = m3u8.M3U8()
    for playlist_name in action['input']:
        playlist_data = playlists['streams'][playlist_name]
        bandwidth = str(playlist_data['bandwidth'])
        m3u8_uri = playlist_data['input-path']
        playlist = m3u8.Playlist(m3u8_uri, stream_info={'bandwidth': bandwidth, 'program_id': '1'}, baseuri="")
        variant_m3u8.add_playlist(playlist)
    variant_m3u8.dump(path + action['output'])
