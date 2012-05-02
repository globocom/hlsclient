from collections import deque

class Balancer(object):
    '''
    Controls witch server is active for a playlist (m3u8)
    '''

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
        self.paths[path].rotate(-1)

    @property
    def actives(self):
        '''
        Returns a list of ``PlaylistResource``s
        '''
        for path, servers in self.paths.items():
            yield PlaylistResource(servers[0], path)


class PlaylistResource(object):
    
    def __init__(self, server, path):
        self.server = server
        self.path = path

    def __str__(self):
        return self.server + self.path

    def __unicode__(self):
        return str(self)
