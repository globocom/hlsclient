import os
import errno
import urllib
import urlparse

import m3u8

def consume(m3u8_uri, destination_path):
    '''
    Given a ``m3u8_uri``, downloads all files to disk
    The remote path structure is maintained under ``destination_path``

    '''
    full_path = build_full_path(destination_path, m3u8_uri)

    playlist = m3u8.load(m3u8_uri)

    resources = collect_resources_to_download(playlist)
    modified = download_resources_to_files(resources, full_path)

    if modified:
        playlist.basepath = build_intermediate_path(m3u8_uri)
        save_m3u8(playlist, m3u8_uri, full_path)

    return modified

def build_intermediate_path(m3u8_uri):
    url_path = urlparse.urlparse(m3u8_uri).path
    return os.path.dirname(url_path)

def build_full_path(destination_path, m3u8_uri):
    intermediate_path = build_intermediate_path(m3u8_uri)[1:] # ignore first "/"
    full_path = os.path.join(destination_path, intermediate_path)
    ensure_directory_exists(full_path)
    return full_path

def ensure_directory_exists(directory):
    try:
        os.makedirs(directory)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise

def collect_resources_to_download(playlist):
    resources = []
    if playlist.key:
        resources.append(playlist.key.absolute_uri)
    resources.extend([segment.absolute_uri for segment in playlist.segments])
    return resources

def download_resources_to_files(resources, destination_path):
    return any([download_to_file(r, destination_path) for r in resources])

def save_m3u8(playlist, m3u8_uri, full_path):
    filename = os.path.join(full_path, os.path.basename(m3u8_uri))
    playlist.dump(filename)

def download_to_file(uri, local_path):
    "Retrives the file if it does not exist locally"
    parsed_url = urlparse.urlparse(uri)
    localpath = os.path.join(local_path, os.path.basename(parsed_url.path))
    if not os.path.exists(localpath):
        urllib.urlretrieve(url=uri, filename=localpath)
        return True
    return False
