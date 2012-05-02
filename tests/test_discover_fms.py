import ConfigParser
import io

from fms import FMS
from hlsclient.discover import discover_fms

def test_should_generate_m3u8_path():
    app = 'live_hls'
    instance = 'appInst'
    event = 'bbb'
    stream = 'cam1'

    expected = '/hls-live/' + app + '/' + instance + \
        '/' + event + '/' + stream + '.m3u8'
    path = discover_fms.m3u8_path(app, instance, event, stream)
    assert expected == path

def test_should_list_streams(monkeypatch):
    fms_server = FMS('example.com', 1111, 'user', 'pass')
    monkeypatch.setattr(fms_server, 'getActiveInstances', lambda:
        {'timestamp': 'Wed May  2 15:23:54 2012',
         'code': 'NetConnection.Call.Success',
         'data': {'_0': 'live_hls/tvglobo'},
         'level': 'status'})
    monkeypatch.setattr(fms_server, 'getLiveStreams', lambda a:
        {'timestamp': 'Wed May  2 15:23:54 2012',
         'code': 'NetConnection.Call.Success',
         'data': {'_1': 'globo', '_0': 'globo'},
         'name': '_defaultRoot_:_defaultVHost_:live_hls::_2',
         'level': 'status'})
    assert {'live_hls/tvglobo': ['globo']} == \
        discover_fms.server_streams(fms_server)

def test_should_list_m3u8_paths(monkeypatch):
    fms_server = FMS('example.com', 1111, 'user', 'pass')
    monkeypatch.setattr(discover_fms, 'server_streams', lambda f:
        {'app/inst': ['stream']})
    assert ['/hls-live/app/inst/stream/stream.m3u8'] == \
        list(discover_fms.server_m3u8_paths(fms_server))

def test_should_discover_paths_from_fms_servers(monkeypatch):
    paths = {
        'server1': ['/path1.m3u8', '/path2.m3u8'],
        'server2': ['/path1.m3u8'],
        'server3': ['/path2.m3u8'],
    }
    def fake_server_m3u8_paths(server):
        return paths[server]

    monkeypatch.setattr(discover_fms, 'server_m3u8_paths',
        fake_server_m3u8_paths)

    expected = {'/path1.m3u8': ['server1', 'server2'],
                '/path2.m3u8': ['server1', 'server3'],
    }
    servers = ['server1', 'server2', 'server3']
    assert expected == discover_fms.discover_from_servers(servers)

def test_should_discover_servers_from_config_file(monkeypatch):
    sample_config = """[discover]
backend = discover.fms
port = 1111
user = user
password = password
servers = backend1.globoi.com
          backend2.globoi.com
          backend3.globoi.com
"""
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(sample_config))
    FAKE_RESPONSE = {'/path': ['server']}
    def fake_discover_from_servers(fms_servers):
        for i, server in enumerate(fms_servers):
            assert server.port == 1111
            assert server.username == 'user'
            assert server.password == 'password'
            assert server.server == 'backend%d.globoi.com' % (i + 1)
        return FAKE_RESPONSE

    monkeypatch.setattr(discover_fms, 'discover_from_servers',
        fake_discover_from_servers)
    assert FAKE_RESPONSE == discover_fms.discover(config)
