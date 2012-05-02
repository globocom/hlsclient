from collections import deque
import datetime

class Balancer(object):
    '''
    Controls witch server is active for a playlist (m3u8)
    '''
    NOT_MODIFIED_TOLERANCE = 2 # in seconds

    def update(self, paths):
        '''
        ``paths`` is a dict returned from ``discover.discover()``
        '''
        self.paths = {}
        self.modified_at = {}
        for path, servers in paths.items():
            self.paths[path] = deque(servers)

    def notify_modified(self, server, path):
        '''
        Remembers that a given server returned a new playlist
        '''
        self.modified_at[path] = datetime.datetime.now()

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
        for path in self.paths:
            active_server = self._active_server_for_path(path)
            if self._outdated(active_server, path):
                self._change_active_server(path)
                active_server = self._active_server_for_path(path)
            yield PlaylistResource(active_server, path)

    def _active_server_for_path(self, path):
        return self.paths[path][0]

    def _change_active_server(self, path):
        self.paths[path].rotate(-1)
        self.modified_at[path] = None

    def _outdated(self, server, path):
        last_change = self.modified_at.get(path, None)
        if not last_change:
            # This server is new, so it can't be obsolete
            return False
        delta_from_last_change = datetime.datetime.now() - last_change
        delta_tolerance = datetime.timedelta(seconds=self.NOT_MODIFIED_TOLERANCE)
        return delta_from_last_change > delta_tolerance


class PlaylistResource(object):
    
    def __init__(self, server, path):
        self.server = server
        self.path = path

    def __str__(self):
        return self.server + self.path

    def __unicode__(self):
        return str(self)
