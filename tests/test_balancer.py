from collections import namedtuple
import datetime
from hlsclient.balancer import Balancer, PlaylistResource

FMS = namedtuple('FMS', ['server', 'port'])

def test_balancer_returns_active_server_if_its_the_only_one():
	PATH = '/path'
	SERVER = FMS('http://server', port=80)
	paths = {PATH: [SERVER]}
	b = Balancer()
	b.update(paths)
	active_playlists = list(b.actives)
	assert 1 == len(active_playlists)
	assert PATH == active_playlists[0].key
	assert SERVER == active_playlists[0].server

def test_balancer_supports_multiple_paths():
	PATH1 = '/path1'
	PATH2 = '/path2'
	SERVER = 'http://server'
	paths = {PATH1: [SERVER], PATH2: [SERVER]}
	b = Balancer()
	b.update(paths)
	paths = sorted(s.key for s in b.actives)
	assert 2 == len(paths)
	assert PATH1 == paths[0]
	assert PATH2 == paths[1]

def test_active_server_changes_if_error_detected():
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2', 'http://server3']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	# Notify that the active server has failed
	assert [SERVERS[0]] == [s.server for s in b.actives]
	b.notify_error()

	# Assert that the backups assume
	assert [SERVERS[1]] == [s.server for s in b.actives]

	b.notify_error()
	assert [SERVERS[2]] == [s.server for s in b.actives]

	# Assert that the first server resumes if backup fails
	b.notify_error()
	assert [SERVERS[0]] == [s.server for s in b.actives]

def test_active_server_does_not_change_if_paths_updated():
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2', 'http://server3']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	# Notify that active server has failed
	b.notify_error()
	assert [SERVERS[1]] == [s.server for s in b.actives]

	b.update(paths)
	assert [SERVERS[1]] == [s.server for s in b.actives]

def test_active_server_does_not_change_if_new_servers_added():
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2', 'http://server3']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	# Notify that active server has failed
	b.notify_error()
	assert [SERVERS[1]] == [s.server for s in b.actives]

	new_servers = ['http://server3', 'http://server4', 'http://server2']
	b.update({PATH: new_servers})
	assert [SERVERS[1]] == [s.server for s in b.actives]

def test_paths_can_be_removed():
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2', 'http://server3']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	b.update({})
	assert [] == list(b.actives)

def test_active_server_changes_if_playlist_not_modified_for_a_while(monkeypatch):
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	now = datetime.datetime.now()

	assert [SERVERS[0]] == [s.server for s in b.actives]
	b.notify_modified()

	# 20 seconds later and playlist has not changed
	monkeypatch.setattr(b, '_now', lambda: now + datetime.timedelta(seconds=20))
	assert [SERVERS[1]] == [s.server for s in b.actives]

	# more 20 seconds later but backup is being updated
	monkeypatch.setattr(b, '_now', lambda: now + datetime.timedelta(seconds=40))
	b.notify_modified()
	assert [SERVERS[1]] == [s.server for s in b.actives]

def test_if_server_fails_for_any_stream_all_streams_should_switch_server():
	PATH1 = '/path1'
	PATH2 = '/path2'
	SERVER1 = 'http://server1'
	SERVER2 = 'http://server2'
	SERVERS = [SERVER1, SERVER2]
	paths = {PATH1: SERVERS, PATH2: SERVERS}
	b = Balancer()
	b.update(paths)

	assert list(b.actives) == [PlaylistResource(SERVER1, PATH1), PlaylistResource(SERVER1, PATH2)]

	b.notify_error()

	assert list(b.actives) == [PlaylistResource(SERVER2, PATH1), PlaylistResource(SERVER2, PATH2)]

def test_notify_error_should_rotate_servers_while_there_are_available_servers():
	PATH1 = '/path1'
	PATH2 = '/path2'
	SERVER1 = 'http://server1'
	SERVER2 = 'http://server2'
	SERVERS = [SERVER1, SERVER2]
	paths = {PATH1: SERVERS, PATH2: SERVERS}
	b = Balancer()
	b.update(paths)

	b.notify_error()
	b.notify_error()
	assert list(b.actives) == [PlaylistResource(SERVER1, PATH1), PlaylistResource(SERVER1, PATH2)]
