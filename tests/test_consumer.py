from collections import namedtuple
from m3u8.model import Segment, Key
import logging
import m3u8
import os
import urllib
import StringIO

import hlsclient.consumer
from .fake_m3u8_server import M3U8_SERVER, M3U8_HOST, M3U8_PORT
from hlsclient import crypto
from hlsclient import helpers
from hlsclient.balancer import Balancer
from hlsclient.discover import Server, get_servers

def test_consumer_should_download_key_file(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/crypto.m3u8', str(tmpdir))
    assert tmpdir.join('/key.bin') in tmpdir.listdir()

def test_consumer_should_download_segments_and_save_on_the_correct_path(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir))
    assert tmpdir.join('/low1.ts') in tmpdir.listdir()
    assert tmpdir.join('/low2.ts') in tmpdir.listdir()

def test_consumer_should_return_falsy_value_if_there_is_no_new_file(tmpdir):
    assert True == bool(hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir)))
    assert False == bool(hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir)))

def test_consumer_should_return_downloaded_files(tmpdir):
    assert [str(tmpdir.join('low1.ts')), str(tmpdir.join('low2.ts'))] == hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir))
    assert False == hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir))

def test_consumer_should_return_false_if_there_is_no_new_file_for_variant_playlist(tmpdir):
    assert True == hlsclient.consumer.consume(M3U8_SERVER + '/variant-playlist.m3u8', str(tmpdir))
    assert False == hlsclient.consumer.consume(M3U8_SERVER + '/variant-playlist.m3u8', str(tmpdir))

def test_consumer_should_do_nothing_if_file_already_exists(tmpdir):
    # We we try to get these chunks from the server, it will fail
    # since they don't exist. Since we create fake ones, hlsclient
    # will not try to download them.
    tmpdir.join('/missing1.ts').write('CHUNK')
    tmpdir.join('/missing2.ts').write('CHUNK')
    assert False == bool(hlsclient.consumer.consume(M3U8_SERVER + '/missing_chunks.m3u8', str(tmpdir)))

def test_consumer_should_create_intermediate_directories(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(tmpdir))
    expected_path = tmpdir.join('live')
    assert expected_path.check()

def test_consumer_should_save_m3u8_file(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir))
    assert tmpdir.join('low.m3u8') in tmpdir.listdir()

def test_consumer_does_not_save_m3u8_file_if_there_is_no_new_segments(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir))
    tmpdir.join('low.m3u8').write('MODIFIED PLAYLIST')
    assert False == bool(hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir)))
    assert 'MODIFIED PLAYLIST' == tmpdir.join('low.m3u8').read()

def test_if_m3u8_is_generated_with_basepath(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(tmpdir))
    expected_path = tmpdir.join('live').join('low.m3u8')
    assert expected_path.check()

def test_consumer_should_save_segments_with_basepath(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(tmpdir))
    m3u8_content = tmpdir.join('live').join('low.m3u8').read()
    expected_path = tmpdir.join('live').join('low1.ts')
    assert expected_path.check()
    assert "/live/low1.ts" in m3u8_content

def test_variant_m3u8_consumption(tmpdir):
    expected_downloaded = [
        'variant-playlist.m3u8',
        'low.m3u8',
        'high.m3u8',
        'low1.ts',
        'low2.ts',
        'high1.ts',
        'high2.ts']

    # all .m3u8 files are prefixed by {M3U8_SERVER} on our fake m3u8 server
    # and they should be converted to our local basepath
    hlsclient.consumer.consume(M3U8_SERVER + '/variant-playlist.m3u8', str(tmpdir))

    resources_downloaded = os.listdir(str(tmpdir))

    assert sorted(expected_downloaded) == sorted(resources_downloaded)
    for fname in expected_downloaded:
        assert M3U8_SERVER not in open(str(tmpdir.join(fname))).read()

# CRYPTO tests

def test_consumer_should_be_able_to_encrypt_and_decrypt_content(tmpdir):
    content = "blabla"
    fake_key = crypto.get_key("fake_key.bin", str(tmpdir))
    assert content == crypto.decrypt(crypto.encrypt(content, fake_key), fake_key)

    # Generate some big data and try it out
    bigcontent = content * 2 * 1024 + content
    bigcontent = '0123456789abcdef'

    contentf = StringIO.StringIO(bigcontent)
    encryptf = crypto.Encrypt(contentf, fake_key)
    decryptf = crypto.Decrypt(encryptf, fake_key)

    decrypted = ''
    data = decryptf.read(1024)
    while data:
        decrypted += data
        data = decryptf.read(1024)

    assert bigcontent == decrypted

def test_key_generated_by_consumer_should_be_saved_on_right_path(tmpdir):
    fake_key = crypto.get_key("fake_key.bin", str(tmpdir))
    crypto.save_new_key(fake_key, str(tmpdir))

    assert tmpdir.join("fake_key.bin") in tmpdir.listdir()
    assert tmpdir.join("fake_key.iv") in tmpdir.listdir()

def test_save_new_key_should_create_iv_file_with_right_content(tmpdir):
    fake_key = crypto.get_key("fake_key.bin", str(tmpdir))
    fake_key.iv.iv = "rsrs"
    crypto.save_new_key(fake_key, str(tmpdir))

    assert 'rsrs' == tmpdir.join('fake_key.iv').read()

def test_consumer_should_be_able_to_encrypt_segments(tmpdir):
    plain_dir = tmpdir.join('plain')
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(plain_dir))

    encrypted_dir = tmpdir.join('encrypted')
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(encrypted_dir), True)

    plain = plain_dir.join('low1.ts').read()
    encrypted = encrypted_dir.join('low1.ts').read()
    m3u8_content = encrypted_dir.join('low.m3u8').read()

    assert encrypted_dir.join("low.bin").check()
    assert 'URI="low.bin"' in m3u8_content
    assert "#EXT-X-VERSION:2" in m3u8_content

    new_key = crypto.get_key_from_disk("low.bin", str(encrypted_dir))
    assert plain == crypto.decrypt(encrypted, new_key)

def test_consumer_should_reuse_existant_key(tmpdir):
    plain_dir = tmpdir.join('plain')
    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(plain_dir))

    encrypted_dir = tmpdir.join('encrypted')

    new_key = crypto.create_key('low.bin')
    os.makedirs(str(encrypted_dir.join('live')))
    crypto.save_new_key(new_key, str(encrypted_dir.join('live')))

    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(encrypted_dir), True)

    plain = plain_dir.join('live').join('low1.ts').read()
    encrypted = encrypted_dir.join('live').join('low1.ts').read()
    m3u8_content = encrypted_dir.join('live').join('low.m3u8').read()

    assert encrypted_dir.join('live').join("low.bin").check()
    assert 'URI="low.bin"' in m3u8_content
    assert "#EXT-X-VERSION:2" in m3u8_content
    assert plain == crypto.decrypt(encrypted, new_key)

def test_consumer_should_be_able_to_decrypt_segments(tmpdir):
    m3u8_uri = M3U8_SERVER + '/crypto.m3u8'
    playlist = m3u8.load(m3u8_uri)

    encrypted_dir = tmpdir.join('encrypted')
    hlsclient.consumer.consume(m3u8_uri, str(encrypted_dir))
    playlist.key.key_value = encrypted_dir.join('key.bin').read()

    plain_dir = tmpdir.join('plain')
    hlsclient.consumer.consume(m3u8_uri, str(plain_dir), None)

    plain = plain_dir.join('encrypted1.ts').read()
    encrypted = encrypted_dir.join('encrypted2.ts').read()
    m3u8_content = plain_dir.join('crypto.m3u8').read()

    assert plain == crypto.decrypt(encrypted, playlist.key)
    assert "#EXT-X-KEY" not in m3u8_content

def test_consumer_should_be_able_to_change_segments_encryption(tmpdir):
    m3u8_uri = M3U8_SERVER + '/crypto.m3u8'
    playlist = m3u8.load(m3u8_uri)

    original_dir = tmpdir.join('original')
    hlsclient.consumer.consume(m3u8_uri, str(original_dir))
    playlist.key.key_value = original_dir.join('key.bin').read()

    new_dir = tmpdir.join('new')
    hlsclient.consumer.consume(m3u8_uri, str(new_dir), True)

    original = original_dir.join('encrypted1.ts').read()
    new = new_dir.join('encrypted2.ts').read()
    m3u8_content = new_dir.join('crypto.m3u8').read()

    assert new_dir.join("crypto.bin").check()
    assert 'URI="crypto.bin"' in m3u8_content

    new_key = crypto.get_key_from_disk("crypto.bin", str(new_dir))
    assert crypto.decrypt(original, playlist.key) == crypto.decrypt(new, new_key)


def test_consumer_should_save_key_on_basepath(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(tmpdir), True)

    m3u8_content = tmpdir.join('live').join('low.m3u8').read()

    assert tmpdir.join('live').join('low.bin').check()
    assert '#EXT-X-KEY:METHOD=AES-128,URI="low.bin",IV=' in m3u8_content

def test_crypto_should_generate_proper_keyname():
    key_name = crypto.get_key_name("http://example.com/path/to/playlist.m3u8")
    assert "playlist.bin" == key_name

# INTEGRATION TESTS: CONSUME FROM BALANCER

def test_consume_from_balancer_should_report_content_modified(tmpdir):
    server = Server(M3U8_HOST, M3U8_PORT)
    playlist = 'low'
    uri = '/low.m3u8'
    playlists = {'streams': {playlist: {'input-path': uri, 'servers': [server]}}}

    modified = []
    b = Balancer()
    b.update(get_servers(playlists))
    b.notify_modified = lambda server, playlist: modified.append([server, playlist])
    hlsclient.consumer.consume_from_balancer(b, playlists, str(tmpdir))
    assert modified == [[server, playlist]]

    expected_created = ['low.m3u8', 'low1.ts', 'low2.ts']
    resources_created = os.listdir(str(tmpdir))
    assert sorted(expected_created) == sorted(resources_created)

def test_consume_from_balancer_should_not_report_content_modified_if_there_are_no_changes(tmpdir):
    server = Server(M3U8_HOST, M3U8_PORT)
    playlist = 'low'
    uri = '/low.m3u8'
    playlists = {'streams': {playlist: {'input-path': uri, 'servers': [server]}}}

    b = Balancer()
    b.update(get_servers(playlists))
    hlsclient.consumer.consume_from_balancer(b, playlists, str(tmpdir))

    modified = []
    b.notify_modified = lambda server, playlist: modified.append([server, playlist])
    hlsclient.consumer.consume_from_balancer(b, playlists, str(tmpdir))
    assert modified == []

def test_consume_from_balancer_should_report_error(tmpdir, monkeypatch):
    server = Server('invalid host', M3U8_PORT)
    playlist = 'low'
    uri = '/low.m3u8'
    playlists = {'streams': {playlist: {'input-path': uri, 'servers': [server]}}}

    errors = []
    b = Balancer()
    b.update(get_servers(playlists))
    b.notify_error = lambda server, playlist: errors.append([server, playlist])
    monkeypatch.setattr(logging, 'warning', lambda warn: 0) # just to hide hlsclient warning
    hlsclient.consumer.consume_from_balancer(b, playlists, str(tmpdir))

    assert errors == [[server, playlist]]

def test_consume_from_balancer_should_transcode_to_audio(tmpdir):
    server = Server(M3U8_HOST, M3U8_PORT)
    playlist = 'real'
    uri = '/real_content.m3u8'
    playlists = {'streams': {playlist: {'input-path': uri, 'servers': [server]}},
                 'actions': [{'type': 'transcode',
                              'input': playlist,
                              'output': {'audio': {
                                            "transcode": {
                                                "path": "transcode.m3u8",
                                                "audio-bitrate": 64000,
                                                "bandwidth": 65000
                                            }
                              }}}]}

    b = Balancer()
    b.update(get_servers(playlists))
    hlsclient.consumer.consume_from_balancer(b, playlists, str(tmpdir))

    expected_created = ['real_content.m3u8', 'sample.ts', 'transcode.m3u8', 'sample.aac']
    resources_created = os.listdir(str(tmpdir))
    assert sorted(expected_created) == sorted(resources_created)

    original_m3u8 = tmpdir.join('real_content.m3u8').read()
    expected_audio_m3u8 = original_m3u8.replace('.ts', '.aac')
    assert expected_audio_m3u8 == tmpdir.join('transcode.m3u8').read()
