from collections import deque
import datetime
import itertools
import logging

from collections import namedtuple
PlaylistResource = namedtuple('PlaylistResource', ['server', 'key'])

class Balancer(object):
    '''
    Controls which server is active for a playlist (m3u8)
    '''
    NOT_MODIFIED_TOLERANCE = 8 # in seconds

    def __init__(self, not_modified_tolerance=None):
        self.NOT_MODIFIED_TOLERANCE = not_modified_tolerance or self.NOT_MODIFIED_TOLERANCE
        self.keys = []
        self.servers = deque()
        self.modified_at = None

    def update(self, keys):
        '''
        ``keys`` is a dict returned from ``discover.get_servers()``
        '''
        self.keys = keys.keys()
        intersection_servers = self._find_set_intersection(keys.values())

        # remove what no longer exists
        for old_server in list(self.servers):
            if old_server not in intersection_servers:
                self.servers.remove(old_server)

        # add new servers
        for new_server in intersection_servers:
            if new_server not in self.servers:
                self.servers.append(new_server)

        self.modified_at = self._now()


    def notify_modified(self):
        '''
        Remembers that a given server returned a new playlist
        '''
        self.modified_at = self._now()

    def notify_error(self):
        '''
        Remembers that a given server failed.
        This immediately changes the active server for this key, is another one exists.
        '''
        self._change_active_server()

    @property
    def actives(self):
        '''
        Returns a list of ``PlaylistResource``s
        '''
        active_server = self._active_server()
        if self._outdated(active_server):
            active_server = self._change_active_server()
        return (PlaylistResource(active_server, key) for key in self.keys)

    def _active_server(self):
        if self.servers:
            return self.servers[0]

    def _rotate_servers(self):
        self.servers.rotate(-1)
        return self._active_server()

    def _change_active_server(self):
        retries = 0
        max_retries = len(self.servers)

        active_server = self._rotate_servers()

        while self._outdated(active_server) and retries < max_retries:
            logging.warning("{server} outdated".format(server=active_server))
            active_server = self._rotate_servers()
            retries += 1

        return self._active_server()

    def _outdated(self, server):
        delta_from_last_change = self._now() - self.modified_at
        delta_tolerance = datetime.timedelta(seconds=self.NOT_MODIFIED_TOLERANCE)
        return delta_from_last_change > delta_tolerance

    def _now(self):
        # The only reason for this to be a method
        # is that it's easier to monkey patch it
        return datetime.datetime.now()

    def _find_set_intersection(self, groups):
        # do not use `set()` because sets are unordered
        # and the server list must preserve order
        flatten = list(itertools.chain(*groups))
        result = []
        for elem in flatten:
            if elem not in result and flatten.count(elem) == len(groups):
                result.append(elem)
        return result