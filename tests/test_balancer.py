from hlsclient.balancer import Balancer

def test_balancer_returns_active_server_if_its_the_only_one():
	paths = {'/path': ['server']}
	b = Balancer()
	b.update(paths)
	active_servers = b.actives
	assert 1 == len(active_servers)
