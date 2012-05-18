import ConfigParser
import io

import hlsclient.discover
from hlsclient.discover import discover, Server

def test_discovers_simple_m3u8_from_api_url_in_config(monkeypatch):
    sample_config = """[discover]
api_url = http://localhost:4422/tests.m3u8
"""
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(sample_config))

    def fake_get_info_from_url(url):
        # m3u8 sample got from http://webme.ws/live-docs/thorp.html
        return [{
            'm3u8': '/hls-without-mbr.m3u8',
            'servers': ['serv1.com', 'serv2.com'],
            'bitrates': [],
            'needs_index': False,
        }]

    monkeypatch.setattr(hlsclient.discover, 'get_info_from_url', fake_get_info_from_url)

    m3u8_path = '/hls-without-mbr.m3u8'
    servers = [Server(server='serv1.com', port=80), Server(server='serv2.com', port=80)]
    assert {m3u8_path: servers} == discover(config)



