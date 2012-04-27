
class Balancer(object):
    '''
    Controls witch server is active for a playlist (m3u8)
    '''

    def update(self, paths):
        '''
        ``paths`` is a dict returned from ``discover.discover()``
        '''
        pass

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
        pass

    @property
    def actives(self):
        '''
        Returns a list of ``PlaylistResource``s
        '''
        return []


class PlaylistResource(object):
    
    def __init__(self, server, path):
        self.server = server
        self.path = path

    def __unicode__(self):
        return self.server + self.path
