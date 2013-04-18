import ConfigParser
import io

import hlsclient.discover
from hlsclient.discover import Server

def test_discovers_simple_m3u8_from_api_url_in_config(monkeypatch):
    sample_config = """[discover]
api_url = http://localhost:4422/tests.m3u8
"""
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(sample_config))

    def fake_get_streams_from_url(url):
        return {"streams": {
                    "hls-without-mbr":
                        {
                            'input-path': '/hls-without-mbr.m3u8',
                            'servers': ['http://serv1.com', 'http://serv2.com'],
                        }
                    }
                }

    monkeypatch.setattr(hlsclient.discover, '_get_streams_from_url', fake_get_streams_from_url)
    paths = hlsclient.discover.discover_playlists(config)['streams']

    servers = [Server(server='http://serv1.com', port=80), Server(server='http://serv2.com', port=80)]
    playlist = {"hls-without-mbr": {'input-path': '/hls-without-mbr.m3u8', 'servers': servers}}

    assert playlist == paths

def test_discovers_multiple_playlists_from_api_url_in_config(monkeypatch):
    sample_config = """[discover]
api_url = http://localhost:4422/mbr-tests.m3u8
"""
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(sample_config))

    def fake_get_streams_from_url(url):
        return {"streams": {
                    "hls100": {
                        'input-path': '/hls100.m3u8',
                        'servers': ['http://serv1.com', 'http://serv2.com:1234'],
                        'bandwidth': 100000,
                    },
                    "hls200": {
                        'input-path': '/hls200.m3u8',
                        'servers': ['http://serv1.com:81', 'http://serv2.com:2345'],
                        'bandwidth': 200000,
                    },
                    "hls300": {
                        'input-path': '/hls300.m3u8',
                        'servers': ['http://serv1.com:82', 'http://serv2.com:3456'],
                        'bandwidth': 300000,
                    }
                }}


    monkeypatch.setattr(hlsclient.discover, '_get_streams_from_url', fake_get_streams_from_url)
    paths = hlsclient.discover.discover_playlists(config)['streams']

    expected_result = {
        'hls100': {
            'input-path': '/hls100.m3u8',
            'servers': [Server('http://serv1.com', port=80), Server('http://serv2.com', 1234)],
            'bandwidth': 100000
        },
        'hls200': {
            'input-path': '/hls200.m3u8',
            'servers': [Server('http://serv1.com', port=81), Server('http://serv2.com', 2345)],
            'bandwidth': 200000
        },
        'hls300': {
            'input-path': '/hls300.m3u8',
            'servers': [Server('http://serv1.com', port=82), Server('http://serv2.com', 3456)],
            'bandwidth': 300000
        }
    }

    assert expected_result == paths

def test_url_to_server_should_handle_https():
    server = hlsclient.discover._url_to_server("https://serv1.com")
    assert 443 == server.port
    assert "https://serv1.com" == server.server

def test_get_servers_from_playlists():
    playlists = {"streams": {"hls100": {'input-path': '/hls100.m3u8', 'servers': ['A', 'B']}}}
    paths = hlsclient.discover.get_servers(playlists)
    assert {'hls100': ['A', 'B']} == paths
