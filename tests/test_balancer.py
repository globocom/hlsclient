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

def test_balancer_supports_multiple_paths():
	PATH1 = '/path1'
	PATH2 = '/path2'
	SERVER = 'server'
	paths = {PATH1: [SERVER], PATH2: [SERVER]}
	b = Balancer()
	b.update(paths)
	paths = sorted(s.path for s in b.actives)
	assert 2 == len(paths)
	assert PATH1 == paths[0]
	assert PATH2 == paths[1]

def test_active_server_changes_if_error_detected():
	PATH = '/path'
	SERVERS = ['server1', 'server2']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	# Notify that active server has failed
	assert [SERVERS[0]] == [s.server for s in b.actives]

	# Assert that the backup assumes
	b.notify_error(SERVERS[0], PATH)
	assert [SERVERS[1]] == [s.server for s in b.actives]

	# Assert that the first server resumes if backup fails
	b.notify_error(SERVERS[1], PATH)
	assert [SERVERS[0]] == [s.server for s in b.actives]
