import m3u8

def consume(m3u8_path, destination_path):
    "Receives a m3u8 path and copies all playlist files to a local path"
    playlist = m3u8.model.M3U8()
    playlist.load(m3u8_path)
    if playlist.key:
        download_to_file(playlist.key.uri, destination_path)

def download_to_file(uri, local_path):
    "Retrives the file if it does not exist locally"
    pass
