from hlsclient.balancer import Balancer

def test_balancer_returns_active_server_if_its_the_only_one():
	PATH = '/path'
	SERVER = 'server'
	paths = {PATH: [SERVER]}
	b = Balancer()
	b.update(paths)
	active_streams = list(b.actives)
	assert 1 == len(active_streams)
	assert PATH == active_streams[0].path
	assert SERVER == active_streams[0].server
	assert SERVER + PATH == str(active_streams[0])
