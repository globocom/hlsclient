from Crypto.Cipher import AES
from pkcs7 import PKCS7Encoder

import errno
import os
import urllib2
import urlparse

import m3u8

def consume(m3u8_uri, destination_path, new_key=False):
    '''
    Given a ``m3u8_uri``, downloads all files to disk
    The remote path structure is maintained under ``destination_path``

    - new_key:
        If False, keeps existing encryption
        If None, decrypts file
    '''
    playlist = m3u8.load(m3u8_uri)

    if playlist.is_variant:
        return consume_variant_playlist(playlist, m3u8_uri, destination_path)
    else:
        return consume_single_playlist(playlist, m3u8_uri, destination_path, new_key)

def consume_variant_playlist(playlist, m3u8_uri, destination_path):
    full_path = build_full_path(destination_path, m3u8_uri)
    for p in playlist.playlists:
        consume(p.absolute_uri, destination_path)
    save_m3u8(playlist, m3u8_uri, full_path)
    return True

def consume_single_playlist(playlist, m3u8_uri, destination_path, new_key=False):
    full_path = build_full_path(destination_path, m3u8_uri)
    downloaded_key = download_key(playlist, destination_path)
    downloaded_segments = download_segments(playlist, full_path, new_key)

    m3u8_has_changed = downloaded_key or any(downloaded_segments)
    if m3u8_has_changed:
        save_m3u8(playlist, m3u8_uri, full_path, new_key)

    return m3u8_has_changed

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

def download_key(playlist, destination_path):
    if playlist.key:
        filename = download_to_file(playlist.key.absolute_uri, destination_path)
        with open(filename, 'rb') as f:
            playlist.key.key_value = f.read()
    return False

def download_segments(playlist, destination_path, new_key):
    segments = [segment.absolute_uri for segment in playlist.segments]
    return [download_to_file(uri, destination_path, playlist.key, new_key) for uri in segments]

def save_m3u8(playlist, m3u8_uri, full_path, new_key=False):
    playlist.basepath = build_intermediate_path(m3u8_uri)
    if new_key:
        save_new_key(new_key, full_path)
        playlist.version = "2"
        playlist.key = new_key
    elif new_key is None:
        playlist.key = None
    filename = os.path.join(full_path, os.path.basename(m3u8_uri))
    playlist.dump(filename)

def save_new_key(new_key, destination_path):
    filename = os.path.join(destination_path, os.path.basename(new_key.uri))
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            f.write(new_key.key_value)

def download_to_file(uri, destination_path, old_key=None, new_key=False):
    '''
    Retrives the file if it does not exist locally and changes the encryption if needed.

    '''
    filename = os.path.join(destination_path, os.path.basename(uri))
    if not os.path.exists(filename):
        request = urllib2.urlopen(url=uri)
        raw = request.read()
        if new_key is not False:
            plain = decrypt(raw, old_key) if old_key else raw
            raw = encrypt(plain, new_key) if new_key else plain
        with open(filename, 'wb') as f:
            f.write(raw)
        return filename
    return False

def random_key(key_name):
    class IV:
        def __init__(self, iv):
            self.iv = iv

        def __str__(self):
            return '0X' + self.iv.encode('hex')

    key = m3u8.model.Key(method='AES-128', uri=key_name, baseuri=None,  iv=IV(os.urandom(16)))
    key.key_value = os.urandom(16)
    return key

def get_key_iv(key):
    iv = str(key.iv)[2:] # Removes 0X prefix
    return iv.decode('hex')

def encrypt(data, key):
    encoder = PKCS7Encoder()
    padded_text = encoder.encode(data)
    encryptor = AES.new(key.key_value, AES.MODE_CBC, get_key_iv(key))
    encrypted_data = encryptor.encrypt(padded_text)

    return encrypted_data

def decrypt(data, key):
    encoder = PKCS7Encoder()
    decryptor = AES.new(key.key_value, AES.MODE_CBC, get_key_iv(key))
    plain = decryptor.decrypt(data)

    return encoder.decode(plain)
