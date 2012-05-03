from collections import namedtuple
import m3u8
import urllib
import os
import shutil

import hlsclient.consumer

Key = namedtuple('Key', 'uri')
Segment = namedtuple('Segment', 'uri')

class BaseFakeM3U8(object):
    @property
    def key(self):
        return None

    @property
    def segments(self):
        return []

def test_if_consume_loads_path(monkeypatch):
    called_args = []
    def fake_load(url):
        called_args.append(url)
        return BaseFakeM3U8()

    monkeypatch.setattr(m3u8, 'load', fake_load)
    hlsclient.consumer.consume('m3u8', '/local_path')
    assert ['m3u8'] == called_args

def test_if_consume_downloads_key_file(monkeypatch):
    class FakeM3U8(BaseFakeM3U8):
        @property
        def key(self):
            return Key('/key')
    monkeypatch.setattr(m3u8, 'load', lambda _: FakeM3U8())

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
    monkeypatch.setattr(m3u8, 'load', lambda _: FakeM3U8())

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
    monkeypatch.setattr(m3u8, 'load', lambda _: FakeM3U8())

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

def test_if_download_to_file_creates_intermediate_directories():
    path_with_intermediate_directories = '/tmp/inter/go/'
    SEGMENT_URI = 'http://example.com/path/subpath/chunk.ts'

    shutil.rmtree(path_with_intermediate_directories, ignore_errors=True)
    hlsclient.consumer.download_to_file(SEGMENT_URI,
            path_with_intermediate_directories)

    assert os.path.exists(path_with_intermediate_directories)
