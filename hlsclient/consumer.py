import m3u8
import os
import urllib
from urlparse import urlparse


def consume(m3u8_path, destination_path):
    "Receives a m3u8 path and copies all playlist files to a local path"
    playlist = m3u8.model.M3U8()
    playlist.load(m3u8_path)

    files_to_download = []
    if playlist.key:
        files_to_download.append(playlist.key.uri)

    files_to_download.extend([segment.uri for segment in playlist.segments])
    downloaded = [download_to_file(f, destination_path) for f
        in files_to_download]
    return any(downloaded)

def download_to_file(uri, local_path):
    "Retrives the file if it does not exist locally"
    remote_path = urlparse(uri).path
    basename = os.path.basename(remote_path)
    localpath = os.path.join(local_path, basename)
    if not os.path.exists(localpath):
        urllib.urlretrieve(url=uri, filename=localpath)
        return True
    return False
