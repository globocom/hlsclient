from Crypto.Cipher import AES
from pkcs7 import PKCS7Encoder
from m3u8.model import Key

from collections import namedtuple
import errno
import os
import urllib
from urlparse import urlparse

MPEG_TS_HEADER = '474000'.decode('hex')

import m3u8

def consume(m3u8_uri, destination_path, new_key=False):
    '''
    Given a ``m3u8_uri``, downloads all files to disk
    The remote path structure is maintained under ``destination_path``

    '''
    full_path = build_full_path(destination_path, m3u8_uri)

    playlist = m3u8.load(m3u8_uri)

    resources = collect_resources_to_download(playlist)
    downloaded_files = download_resources_to_files(resources, full_path)

    if downloaded_files:
        if new_key:
            # TODO: Key substitution is not tested!
            save_new_key(new_key, destination_path)
            change_segments_key(downloaded_files, playlist.key, random_key())
            playlist.key = new_key
            playlist.data['version'] = "2"

        playlist.basepath = build_intermediate_path(m3u8_uri)
        save_m3u8(playlist, m3u8_uri, full_path)

    return downloaded_files

def build_intermediate_path(m3u8_uri):
    url_path = urlparse(m3u8_uri).path
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
        resources.append(playlist.key.uri)
    resources.extend([segment.uri for segment in playlist.segments])
    return resources

def download_resources_to_files(resources, destination_path):
    downloaded_paths = map(lambda r: download_to_file(r, destination_path), resources)
    return filter(None, downloaded_paths)

def save_m3u8(playlist, m3u8_uri, full_path):
    filename = os.path.join(full_path, os.path.basename(m3u8_uri))
    playlist.dump(filename)

def download_to_file(uri, destination_path):
    "Retrives the file if it does not exist locally"
    filename = os.path.join(destination_path, os.path.basename(uri))
    if not os.path.exists(filename):
        urllib.urlretrieve(url=uri, filename=filename)
        return filename
    return False


# TODO: All methods below don't have unittests!

def random_key():
    class IV:
        def __init__(self, iv):
            self.iv = iv

        def __str__(self):
            return '0X' + self.iv.encode('hex')

    key = Key(method='AES-128', uri='/tmp/hls/mykey.bin', iv=IV(os.urandom(16)))
    key.key = os.urandom(16)
    key.basepath = '/tmp/hls'
    return key

def save_new_key(key, destination_path):
    filename = os.path.join(destination_path, os.path.basename(key.uri))
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(key.key)

def change_segments_key(paths, original_key, new_key):
    for path in paths:
        if path.endswith('.ts'): # TODO: refactor, get only segments
            change_segment_key(path, original_key, new_key)

def change_segment_key(path, original_key, new_key):
    plain = get_plain_segment_content(path, original_key)
    encoder = PKCS7Encoder()
    padded_text = encoder.encode(plain)
    encryptor = AES.new(new_key.key, AES.MODE_CBC, new_key.iv.iv)
    encrypted = encryptor.encrypt(padded_text)
    with open(path, "w") as f:
        f.write(encrypted)
    assert plain == get_plain_segment_content(path, new_key)

def get_plain_segment_content(segment_path, key):
    with open(segment_path, "r") as f:
        raw = f.read()
    if key:
        # This has not been tested even manually
        with open(str(key.uri), "r") as f:
            key_value = f.read()
        iv = key.iv[2:].decode('hex') # Removes 0X prefix
        decryptor = AES.new(key_value, AES.MODE_CBC, iv)
        plain = decryptor.decrypt(raw)
    else:
        plain = raw
    assert plain.startswith(MPEG_TS_HEADER)
    return plain
