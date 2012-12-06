import errno
import os
import logging
import urllib2
import httplib
import urlparse
import m3u8
import shutil
import tempfile

import crypto
from futures import ThreadPoolExecutor

from hlsclient.transcode import transcode_playlist
from hlsclient import helpers

config = helpers.load_config()
NUM_THREAD_WORKERS = config.getint('hlsclient', 'num_thread_workers')
DOWNLOAD_TIMEOUT = config.getint('hlsclient', 'download_timeout')

def consume_from_balancer(balancer, playlists, destination, encrypt=False):
    '''
    Consume all active playlist resources from ``balancer`` and
    report status to it.

    '''
    def consume_resource(playlist_resource):
        m3u8_uri = "{server}:{port}{path}".format(
            server=playlist_resource.server.server,
            port=playlist_resource.server.port,
            path=playlists['streams'][playlist_resource.key]['input-path'])
        try:
            modified = consume(m3u8_uri, destination, encrypt)
        except (httplib.HTTPException, urllib2.HTTPError, IOError, OSError) as err:
            logging.warning(u'Notifying error for resource %s: %s' % (m3u8_uri, err))
            balancer.notify_error(playlist_resource.server, playlist_resource.key)
        else:
            if modified:
                logging.info('Notifying content modified: %s' % m3u8_uri)
                balancer.notify_modified(playlist_resource.server, playlist_resource.key)
                m3u8_path = os.path.join(build_full_path(destination, m3u8_uri), os.path.basename(m3u8_uri))
                transcode_playlist(playlists, playlist_resource.key, modified, m3u8_path)
            else:
                logging.debug('Content not modified: %s' % m3u8_uri)
    with ThreadPoolExecutor(max_workers=NUM_THREAD_WORKERS) as executor:
        list(executor.map(consume_resource, balancer.actives))

def consume(m3u8_uri, destination_path, encrypt=False):
    '''
    Given a ``m3u8_uri``, downloads all files to disk
    The remote path structure is maintained under ``destination_path``

    - encrypt:
        If False, keeps existing encryption
        If None, decrypts file
        If True, a new key is created

    '''
    logging.debug('Consuming %s' % m3u8_uri)
    playlist = m3u8.load(m3u8_uri)

    if playlist.is_variant:
        return consume_variant_playlist(playlist, m3u8_uri, destination_path, encrypt)
    else:
        return consume_single_playlist(playlist, m3u8_uri, destination_path, encrypt)

def consume_variant_playlist(playlist, m3u8_uri, destination_path, encrypt=False):
    changed = False
    full_path = build_full_path(destination_path, m3u8_uri)
    for p in playlist.playlists:
        changed |= bool(consume(p.absolute_uri, destination_path, encrypt))
    save_m3u8(playlist, m3u8_uri, full_path)
    return changed

def consume_single_playlist(playlist, m3u8_uri, destination_path, encrypt=False):
    full_path = build_full_path(destination_path, m3u8_uri)

    if encrypt:
        key_name = crypto.get_key_name(m3u8_uri)
        new_key = crypto.get_key(key_name, full_path)
    else:
        new_key = encrypt

    downloaded_key = download_key(playlist, full_path, new_key)
    downloaded_segments = download_segments(playlist, full_path, new_key)

    m3u8_has_changed = downloaded_key or any(downloaded_segments)
    if m3u8_has_changed:
        save_m3u8(playlist, m3u8_uri, full_path, new_key)
        return filter(None, downloaded_segments)

    return False

def build_intermediate_path(m3u8_uri):
    '''
    Returns the original m3u8 base path

    '''
    url_path = urlparse.urlparse(m3u8_uri).path
    return os.path.dirname(url_path)

def build_full_path(destination_path, m3u8_uri):
    '''
    Returns the path where the m3u8, ts and bin will be saved.

    '''
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

def download_segments(playlist, destination_path, new_key):
    uris = [segment.absolute_uri for segment in playlist.segments]

    def download(uri):
        try:
            return download_to_file(uri, destination_path, playlist.key, new_key)
        except urllib2.HTTPError as err:
            if err.code == 404:
                logging.warning(u'Got 404 trying to download %s' % (uri,))
                return None
            raise

    with ThreadPoolExecutor(max_workers=NUM_THREAD_WORKERS) as executor:
        downloads = executor.map(download, uris)
        return list(downloads)

def save_m3u8(playlist, m3u8_uri, full_path, new_key=False):
    '''
    Saves the m3u8, updating the key if needed

    - new_key:
        If False, keeps existing encryption
        If None, decrypts file
        If any other value, this value is set

    '''
    playlist.basepath = build_intermediate_path(m3u8_uri)
    if new_key:
        crypto.save_new_key(new_key, full_path)
        playlist.version = "2"
        playlist.key = new_key
    elif new_key is None:
        playlist.key = None
    filename = os.path.join(full_path, os.path.basename(m3u8_uri))
    atomic_dump(playlist, filename)

def atomic_dump(playlist, filename):
    _, tmp_filename = tempfile.mkstemp(dir=os.path.dirname(filename))
    playlist.dump(tmp_filename)
    os.rename(tmp_filename, filename)

def download_key(playlist, destination_path, new_key):
    if playlist.key:
        filename = download_to_file(playlist.key.absolute_uri, destination_path)
        with open(filename, 'rb') as f:
            playlist.key.key_value = f.read()
        return True

def download_to_file(uri, destination_path, current_key=None, new_key=False):
    '''
    Retrives the file if it does not exist locally and changes the encryption if needed.

    '''
    filename = os.path.join(destination_path, os.path.basename(uri))
    if not os.path.exists(filename):
        logging.debug("Downloading {url}".format(url=uri))
        raw = urllib2.urlopen(url=uri, timeout=DOWNLOAD_TIMEOUT)
        if new_key is not False:
            plain = crypto.Decrypt(raw, current_key) if current_key else raw
            raw = crypto.Encrypt(plain, new_key) if new_key else plain
        atomic_write(raw, filename)
        return filename
    else:
        # change modification time so the file is not removed by hlsclient.cleaner.clean
        os.utime(filename, None)
    return False

def atomic_write(content, filename):
    _, tmp_filename = tempfile.mkstemp(dir=os.path.dirname(filename))
    with open(tmp_filename, 'wb') as f:
        shutil.copyfileobj(content, f)
    os.rename(tmp_filename, filename)
