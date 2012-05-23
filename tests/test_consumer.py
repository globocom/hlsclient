from collections import namedtuple
import urllib
import os
import m3u8
from m3u8.model import Segment, Key

import hlsclient.consumer
from hlsclient.consumer import collect_resources_to_download, encrypt, decrypt, random_key
from .fake_m3u8_server import M3U8_SERVER

class BaseFakeM3U8(object):
    _m3u8_saved_path = None
    is_variant = False

    @property
    def key(self):
        return None

    @property
    def segments(self):
        return []

    def dump(self, path):
        self._m3u8_saved_path = path

def test_if_consume_loads_path(monkeypatch, tmpdir):
    called_args = []
    def fake_load(url):
        called_args.append(url)
        return BaseFakeM3U8()

    monkeypatch.setattr(m3u8, 'load', fake_load)
    hlsclient.consumer.consume('m3u8', str(tmpdir.join('local_path')))
    assert ['m3u8'] == called_args

def test_if_consume_downloads_key_file(monkeypatch, tmpdir):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def key(self):
            return Key(method='AES', uri='/key', baseuri='http://example.com')
    monkeypatch.setattr(m3u8, 'load', lambda _: FakeM3U8())

    called_args = []
    def fake_download_to_file(uri, local_path):
        assert 'http://example.com/key' == uri
        called_args.append(uri)
        return True
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file',
        fake_download_to_file)
    assert hlsclient.consumer.consume('m3u8', str(tmpdir.join('local_path')))
    assert 1 == len(called_args)

def test_if_consume_downloads_segments_and_saves_on_the_correct_path(monkeypatch, tmpdir):
    REMOTE_CHUNKS = ['http://server/another/remote/location/chunk1.ts',
                     'http://server/another/remote/location/chunk2.ts']

    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri=uri, baseuri='http://exaple.com') for uri in REMOTE_CHUNKS]
    monkeypatch.setattr(m3u8, 'load', lambda _: FakeM3U8())

    called_args = []
    def fake_download_to_file(uri, local_path):
        assert local_path == str(tmpdir.join('local_path', 'remote', 'path'))
        called_args.append(uri)
        return True
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file',
        fake_download_to_file)

    assert hlsclient.consumer.consume('http://server/remote/path/m3u8', str(tmpdir.join('local_path')))
    assert REMOTE_CHUNKS == called_args

def test_if_consume_returns_false_if_there_is_no_new_file(monkeypatch, tmpdir):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri='/path1', baseuri='http://exaple.com'),
                    Segment(uri='/path2', baseuri='http://exaple.com')]
    monkeypatch.setattr(m3u8, 'load', lambda _: FakeM3U8())

    def fake_download_to_file(uri, local_path):
        return False
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file',
        fake_download_to_file)
    assert not hlsclient.consumer.consume('m3u8', str(tmpdir.join('local_path')))

def test_if_download_to_file_saves_the_file_with_correct_path(monkeypatch):
    called_args = []
    def fake_urlretrieve(url, filename):
        called_args.append([url, filename])
    monkeypatch.setattr(urllib, 'urlretrieve', fake_urlretrieve)

    SEGMENT_URI = 'http://example.com/path/subpath/chunk.ts'
    hlsclient.consumer.download_to_file(SEGMENT_URI, '/tmp/')
    assert 1 == len(called_args)
    assert SEGMENT_URI == called_args[0][0]
    assert '/tmp/chunk.ts' == called_args[0][1]

def test_if_download_to_file_does_nothing_if_file_already_exists(monkeypatch):
    called_args = []
    def fake_urlretrieve(url, filename):
        called_args.append([url, filename])
    monkeypatch.setattr(urllib, 'urlretrieve', fake_urlretrieve)

    def fake_exists(path):
        return True
    monkeypatch.setattr(os.path, 'exists', fake_exists)

    SEGMENT_URI = 'http://example.com/path/subpath/chunk.ts'
    hlsclient.consumer.download_to_file(SEGMENT_URI, '/tmp/')
    assert 0 == len(called_args)

def test_if_download_to_file_creates_intermediate_directories(monkeypatch, tmpdir):
    monkeypatch.setattr(m3u8, 'load', lambda _: BaseFakeM3U8())
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file', lambda *args: True)

    destination_path = tmpdir.join('subdir1', 'subdir2')
    hlsclient.consumer.consume('http://server.com/live/stream.m3u8', str(destination_path))

    expected_path = destination_path.join('live')

    assert expected_path.check()

def test_if_consume_saves_m3u8_file_if_new_segment_saved(monkeypatch, tmpdir):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri='/path1', baseuri='http://exaple.com'),
                    Segment(uri='/path2', baseuri='http://exaple.com')]

    fake_m3u8 = FakeM3U8()

    monkeypatch.setattr(m3u8, 'load', lambda _: fake_m3u8)
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file', lambda *args: True)

    hlsclient.consumer.consume('http://server/remote/path/file.m3u8', str(tmpdir.join('local_path')))
    # ignore existing
    hlsclient.consumer.consume('http://server/remote/path/file.m3u8', str(tmpdir.join('local_path')))

    local_path = tmpdir.join('local_path', 'remote', 'path')
    assert local_path.join('file.m3u8') == fake_m3u8._m3u8_saved_path

def test_if_consume_does_not_save_m3u8_file_if_no_segment_saved(monkeypatch, tmpdir):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri='/path1', baseuri='http://exaple.com'),
                    Segment(uri='/path2', baseuri='http://exaple.com')]

    fake_m3u8 = FakeM3U8()

    monkeypatch.setattr(m3u8, 'load', lambda _: fake_m3u8)
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file', lambda *args: False)

    hlsclient.consumer.consume('m3u8', str(tmpdir.join('local_path')))

    assert not fake_m3u8._m3u8_saved_path

def test_if_m3u8_is_generated_with_basepath(monkeypatch, tmpdir):
    M3U8_PATH = '/remote/path'
    M3U8_URI = 'http://server.com' + M3U8_PATH + '/file.m3u8'
    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri='/path1', baseuri='http://exaple.com'),
                    Segment(uri='/path2', baseuri='http://exaple.com')]

    fake_m3u8 = FakeM3U8()
    monkeypatch.setattr(m3u8, 'load', lambda _: fake_m3u8)
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file', lambda *args: True)
    hlsclient.consumer.consume(M3U8_URI, str(tmpdir.join('local_path')))

    assert M3U8_PATH == fake_m3u8.basepath

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
    fake_key = random_key()
    assert content == decrypt(encrypt(content, fake_key), fake_key)
