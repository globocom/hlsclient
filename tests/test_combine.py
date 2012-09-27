import ConfigParser
import io
import os

import hlsclient.discover
import hlsclient.combine
from tests.fake_m3u8_server import VARIANT_PLAYLIST, M3U8_SERVER


def test_combine_variant_playlists(tmpdir):
    variant_config = """[discover]
api_url = {host}/variant.json
""".format(host=M3U8_SERVER)
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(variant_config))

    paths = hlsclient.discover.discover_playlists(config)
    hlsclient.combine.combine_playlists(paths, str(tmpdir))

    filepath = str(tmpdir.join('hls-with-mbr.m3u8'))
    assert os.path.exists(filepath)
    assert VARIANT_PLAYLIST == open(filepath).read()
