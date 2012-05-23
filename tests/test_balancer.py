from collections import namedtuple
import datetime
from hlsclient.balancer import Balancer

FMS = namedtuple('FMS', ['server', 'port'])

def test_balancer_returns_active_server_if_its_the_only_one():
	PATH = '/path'
	SERVER = FMS('http://server', port=80)
	paths = {PATH: [SERVER]}
	b = Balancer()
	b.update(paths)
	active_playlists = list(b.actives)
	assert 1 == len(active_playlists)
	assert PATH == active_playlists[0].path
	assert SERVER == active_playlists[0].server
	assert SERVER.server + ':' + str(SERVER.port) + PATH == str(active_playlists[0])

def test_balancer_supports_multiple_paths():
	PATH1 = '/path1'
	PATH2 = '/path2'
	SERVER = 'http://server'
	paths = {PATH1: [SERVER], PATH2: [SERVER]}
	b = Balancer()
	b.update(paths)
	paths = sorted(s.path for s in b.actives)
	assert 2 == len(paths)
	assert PATH1 == paths[0]
	assert PATH2 == paths[1]

def test_active_server_changes_if_error_detected():
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2', 'http://server3']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	# Notify that active server has failed
	assert [SERVERS[0]] == [s.server for s in b.actives]
	b.notify_error(SERVERS[0], PATH)

	# Assert that the backups assume
	assert [SERVERS[1]] == [s.server for s in b.actives]

	b.notify_error(SERVERS[1], PATH)
	assert [SERVERS[2]] == [s.server for s in b.actives]

	# Assert that the first server resumes if backup fails
	b.notify_error(SERVERS[2], PATH)
	assert [SERVERS[0]] == [s.server for s in b.actives]

def test_active_server_does_not_change_if_backup_fails():
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	# Notify that the BACKUP server has failed
	assert [SERVERS[0]] == [s.server for s in b.actives]
	b.notify_error(SERVERS[1], PATH)

	# Assert that the active server remains the same
	assert [SERVERS[0]] == [s.server for s in b.actives]

def test_active_server_changes_if_playlist_not_modified_for_a_while(monkeypatch):
	PATH = '/path'
	SERVERS = ['http://server1', 'http://server2']
	paths = {PATH: SERVERS}
	b = Balancer()
	b.update(paths)

	now = datetime.datetime.now()

	assert [SERVERS[0]] == [s.server for s in b.actives]
	b.notify_modified(SERVERS[0], PATH)

	# 20 seconds later and playlist has not changed
	monkeypatch.setattr(b, '_now', lambda: now + datetime.timedelta(seconds=20))
	assert [SERVERS[1]] == [s.server for s in b.actives]

	# more 20 seconds later but backup is being updated
	monkeypatch.setattr(b, '_now', lambda: now + datetime.timedelta(seconds=40))
	b.notify_modified(SERVERS[1], PATH)
	assert [SERVERS[1]] == [s.server for s in b.actives]
