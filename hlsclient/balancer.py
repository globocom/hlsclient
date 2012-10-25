from collections import deque
import datetime
import logging

from collections import namedtuple
PlaylistResource = namedtuple('PlaylistResource', ['server', 'key'])

class Balancer(object):
    '''
    Controls which server is active for a playlist (m3u8)
    '''
    NOT_MODIFIED_TOLERANCE = 8 # in seconds

    def __init__(self, not_modified_tolerance=None):
        if not_modified_tolerance:
            self.NOT_MODIFIED_TOLERANCE = not_modified_tolerance
        self.keys = {}
        self.modified_at = {}

    def update(self, keys):
        '''
        ``keys`` is a dict returned from ``discover.discover()``
        '''
        self._clean_removed_keys(keys)
        for key, servers in keys.items():
            self._update_key(key, servers)

    def notify_modified(self, server, key):
        '''
        Remembers that a given server returned a new playlist
        '''
        self.modified_at[key] = self._now()

    def notify_error(self, server, key):
        '''
        Remembers that a given server failed.
        This immediately changes the active server for this key, is another one exists.
        '''
        if self._active_server_for_key(key) == server:
            self._change_active_server(key)

    @property
    def actives(self):
        '''
        Returns a list of ``PlaylistResource``s
        '''
        for key in self.keys:
            active_server = self._active_server_for_key(key)
            if self._outdated(active_server, key):
                logging.warning("{server} outdated for stream {key}".format(server=active_server, key=key))
                self._change_active_server(key)
                active_server = self._active_server_for_key(key)
            yield PlaylistResource(active_server, key)

    def _clean_removed_keys(self, new_keys):
        removed_keys = set(self.keys.keys()).difference(new_keys.keys())
        for key in removed_keys:
            del self.modified_at[key]
            del self.keys[key]

    def _update_key(self, key, servers):
        active = self._active_server_for_key(key)
        if active in servers:
            self.keys[key] = deque([active])
            self.keys[key].extend([server for server in servers if server != active])
        else:
            self.keys[key] = deque(servers)
            self.modified_at[key] = None

    def _active_server_for_key(self, key):
        servers = self.keys.get(key, [])
        if servers:
            return servers[0]

    def _change_active_server(self, key):
        self.keys[key].rotate(-1)
        self.modified_at[key] = None

    def _outdated(self, server, key):
        last_change = self.modified_at.get(key, None)
        if not last_change:
            # This server is new, so it can't be obsolete
            return False
        delta_from_last_change = self._now() - last_change
        delta_tolerance = datetime.timedelta(seconds=self.NOT_MODIFIED_TOLERANCE)
        return delta_from_last_change > delta_tolerance

    def _now(self):
        # The only reason for this to be a method
        # is that it's easier to monkey patch it
        return datetime.datetime.now()
