from collections import namedtuple
import m3u8
import urllib

import hlsclient.consumer

Key = namedtuple('Key', 'uri')
Segment = namedtuple('Segment', 'uri')

class BaseFakeM3U8(object):
    def load(self, uri):
        pass

    @property
    def key(self):
        return None

    @property
    def segments(self):
        return []

def test_if_consume_loads_path(monkeypatch):
    called_args = []
    class FakeM3U8(BaseFakeM3U8):
        def load(self, url):
            called_args.append(url)

    monkeypatch.setattr(m3u8.model, 'M3U8', FakeM3U8)
    hlsclient.consumer.consume('m3u8', '/local_path')
    assert ['m3u8'] == called_args

def test_if_consume_downloads_key_file(monkeypatch):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def key(self):
            return Key('/key')
    monkeypatch.setattr(m3u8.model, 'M3U8', FakeM3U8)

    called_args = []
    def fake_download_to_file(uri, local_path):
        assert '/key' == uri
        assert local_path == '/local_path'
        called_args.append(uri)
        return True
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file',
        fake_download_to_file)
    assert hlsclient.consumer.consume('m3u8', '/local_path')
    assert 1 == len(called_args)

def test_if_consume_downloads_segments(monkeypatch):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri='/path1'),
                    Segment(uri='/path2')]
    monkeypatch.setattr(m3u8.model, 'M3U8', FakeM3U8)

    called_args = []
    def fake_download_to_file(uri, local_path):
        assert local_path == '/path'
        called_args.append(uri)
        return True
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file',
        fake_download_to_file)
    assert hlsclient.consumer.consume('m3u8', '/path')
    assert ['/path1', '/path2'] == called_args

def test_if_consume_returns_false_if_there_is_no_new_file(monkeypatch):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def segments(self):
            return [Segment(uri='/path1'),
                    Segment(uri='/path2')]
    monkeypatch.setattr(m3u8.model, 'M3U8', FakeM3U8)

    def fake_download_to_file(uri, local_path):
        return False
    monkeypatch.setattr(hlsclient.consumer, 'download_to_file',
        fake_download_to_file)
    assert not hlsclient.consumer.consume('m3u8', '/path')

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
