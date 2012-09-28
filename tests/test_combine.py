import ConfigParser
import io
import os

import hlsclient.discover
import hlsclient.combine
from tests.fake_m3u8_server import VARIANT_PLAYLIST, TRANSCODED_PLAYLIST, M3U8_SERVER


def test_combine_variant_playlists(tmpdir):
    config = read_fake_config('variant.json')
    paths = hlsclient.discover.discover_playlists(config)
    hlsclient.combine.combine_playlists(paths, str(tmpdir))

    filepath = str(tmpdir.join('hls-with-mbr.m3u8'))
    assert os.path.exists(filepath)
    assert VARIANT_PLAYLIST == open(filepath).read()


def test_combine_transcoded_stream_into_variant_playlists(tmpdir):
    config = read_fake_config('transcode.json')
    paths = hlsclient.discover.discover_playlists(config)
    hlsclient.combine.combine_playlists(paths, str(tmpdir))

    filepath = str(tmpdir.join('/nasa/nasa_mbr.m3u8'))
    assert os.path.exists(filepath)
    assert TRANSCODED_PLAYLIST == open(filepath).read()


def read_fake_config(uri):
    variant_config = """[discover]
api_url = {host}/{uri}
""".format(host=M3U8_SERVER, uri=uri)
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(variant_config))
    return config
