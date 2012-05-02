from collections import deque

class Balancer(object):
    '''
    Controls witch server is active for a playlist (m3u8)
    '''
    NOT_MODIFIED_TOLERANCE = 10 # in seconds

    def update(self, paths):
        '''
        ``paths`` is a dict returned from ``discover.discover()``
        '''
        self.paths = {}
        for path, servers in paths.items():
            self.paths[path] = deque(servers)

    def notify_modified(self, server, path):
        '''
        Remembers that a given server returned a new playlist
        '''
        pass

    def notify_error(self, server, path):
        '''
        Remembers that a given server failed.
        This immediately changes the active server for this path, is another one exists.
        '''
        if self._active_server_for_path(path) == server:
            self._change_active_server(path)

    @property
    def actives(self):
        '''
        Returns a list of ``PlaylistResource``s
        '''
        for path, servers in self.paths.items():
            yield PlaylistResource(servers[0], path)

    def _active_server_for_path(self, path):
        return self.paths[path][0]

    def _change_active_server(self, path):
        self.paths[path].rotate(-1)


class PlaylistResource(object):
    
    def __init__(self, server, path):
        self.server = server
        self.path = path

    def __str__(self):
        return self.server + self.path

    def __unicode__(self):
        return str(self)
