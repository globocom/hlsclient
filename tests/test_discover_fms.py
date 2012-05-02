from hlsclient.discover import fms

def test_m3u8_path():
	server = 'example.com'
	app = 'live_hls'
	instance = 'appInst'
	event = 'bbb'
	stream = 'cam1'

	expected = 'http://' + server + '/hls-live/' + app + '/' + \
		instance + '/' + event + '/' + stream + '.m3u8'
	path = fms.m3u8_path(server, app, instance, event, stream)
	assert expected == path
