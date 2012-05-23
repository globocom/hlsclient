from collections import namedtuple
import urllib
import os
import m3u8
from m3u8.model import Segment, Key

import hlsclient.consumer
from hlsclient.consumer import collect_resources_to_download, encrypt, decrypt, random_key, save_new_key
from .fake_m3u8_server import M3U8_SERVER

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

def test_consume_playlist_with_relative_paths():
    playlist = m3u8.M3U8('''\
#EXTM3U
#EXT-X-TARGETDURATION:400
#EXT-X-KEY:METHOD=AES-128,URI="../key.bin", IV=0X10ef8f758ca555115584bb5b3c687f52
#EXTINF:100,
/chunk1.ts
#EXTINF:100,
../chunk2.ts
#EXTINF:100,
../../chunk3.ts
#EXTINF:100,
chunk4.ts
#EXT-X-ENDLIST
''', baseuri='http://example.com/path/to/')
    expected_resources = [
        'http://example.com/path/key.bin',
        'http://example.com/path/to/chunk1.ts',
        'http://example.com/path/chunk2.ts',
        'http://example.com/chunk3.ts',
        'http://example.com/path/to/chunk4.ts',
    ]
    assert expected_resources == collect_resources_to_download(playlist)



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

def test_consumer_should_be_able_to_encrypt_and_decrypt_content():
    content = "blabla"
    fake_key = random_key("fake_key.bin")
    assert content == decrypt(encrypt(content, fake_key), fake_key)

def test_key_generated_by_consumer_should_be_saved_on_right_path(tmpdir):
    fake_key = random_key("fake_key.bin")
    save_new_key(fake_key, str(tmpdir))

    assert tmpdir.join("fake_key.bin") in tmpdir.listdir()

