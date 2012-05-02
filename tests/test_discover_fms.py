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
