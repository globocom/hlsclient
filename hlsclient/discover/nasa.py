from collections import namedtuple
Server = namedtuple('Server', ['server', 'port'])

def discover(config):
    server = Server(server='liveips.nasa.gov.edgesuite.net', port=80)
    return {'/msfc/Edge.m3u8': [server]}