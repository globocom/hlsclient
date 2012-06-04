from collections import namedtuple
import urllib
import os
import m3u8
from m3u8.model import Segment, Key

import hlsclient.consumer
from hlsclient.consumer import encrypt, decrypt, KeyManager
from .fake_m3u8_server import M3U8_SERVER
from hlsclient import helpers

def test_consumer_should_download_key_file(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/crypto.m3u8', str(tmpdir))
    assert tmpdir.join('/key.bin') in tmpdir.listdir()

def test_consumer_should_download_segments_and_save_on_the_correct_path(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir))
    assert tmpdir.join('/low1.ts') in tmpdir.listdir()
    assert tmpdir.join('/low2.ts') in tmpdir.listdir()

def test_consumer_should_return_false_if_there_is_no_new_file(tmpdir):
    assert True == bool(hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir)))
    assert False == bool(hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(tmpdir)))

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

def test_consumer_should_be_able_to_encrypt_and_decrypt_content(tmpdir):
    content = "blabla"
    key_manager = KeyManager()
    fake_key = key_manager.get_key("fake_key.bin", str(tmpdir))
    assert content == decrypt(encrypt(content, fake_key), fake_key)

def test_key_generated_by_consumer_should_be_saved_on_right_path(tmpdir):
    key_manager = KeyManager()
    fake_key = key_manager.get_key("fake_key.bin", str(tmpdir))
    key_manager.save_new_key(fake_key, str(tmpdir))

    assert tmpdir.join("fake_key.bin") in tmpdir.listdir()
    assert tmpdir.join("fake_key.iv") in tmpdir.listdir()

def test_save_new_key_should_create_iv_file_with_right_content(tmpdir):
    key_manager = KeyManager()
    fake_key = key_manager.get_key("fake_key.bin", str(tmpdir))
    fake_key.iv.iv = "rsrs"
    key_manager.save_new_key(fake_key, str(tmpdir))

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

    key_manager = KeyManager()
    new_key = key_manager.get_key_from_disk("low.bin", str(encrypted_dir))
    assert plain == decrypt(encrypted, new_key)

def test_consumer_should_reuse_existant_key(tmpdir):
    plain_dir = tmpdir.join('plain')
    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(plain_dir))

    encrypted_dir = tmpdir.join('encrypted')

    key_manager = KeyManager()
    new_key = key_manager.create_key('low.bin')
    os.makedirs(str(encrypted_dir))
    key_manager.save_new_key(new_key, str(encrypted_dir))

    hlsclient.consumer.consume(M3U8_SERVER + '/low.m3u8', str(encrypted_dir), True)

    plain = plain_dir.join('low1.ts').read()
    encrypted = encrypted_dir.join('low1.ts').read()
    m3u8_content = encrypted_dir.join('low.m3u8').read()

    assert encrypted_dir.join("low.bin").check()
    assert 'URI="low.bin"' in m3u8_content
    assert "#EXT-X-VERSION:2" in m3u8_content
    assert plain == decrypt(encrypted, new_key)

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

    assert plain == decrypt(encrypted, playlist.key)
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

    key_manager = KeyManager()
    new_key = key_manager.get_key_from_disk("crypto.bin", str(new_dir))
    assert decrypt(original, playlist.key) == decrypt(new, new_key)


def test_consumer_should_save_key_on_basepath(tmpdir):
    hlsclient.consumer.consume(M3U8_SERVER + '/live/low.m3u8', str(tmpdir), True)

    m3u8_content = tmpdir.join('live').join('low.m3u8').read()

    assert tmpdir.join('live').join('low.bin').check()
    assert '#EXT-X-KEY:METHOD=AES-128,URI="low.bin",IV=' in m3u8_content

def test_KeyManager_should_have_destination_path(monkeypatch):
    config = helpers.load_config()
    expected = config.get('hlsclient', 'destination')
    key_manager = KeyManager()
    assert expected == key_manager.destination

def test_KeyManager_should_generate_proper_keyname():
    key_manager = KeyManager()
    key_name = key_manager.get_key_name("http://example.com/path/to/playlist.m3u8")
    assert "playlist.bin" == key_name
