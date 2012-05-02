def discover(config):
    '''
    Receives the extra configuration parameters from [discover] section

    Returns a dictionary with format:

      {'/path1.m3u8': ['server1', 'server2'],
       '/path2.m3u8': ['server3', 'server4', 'server5']}

    '''
    raise NotImplementedError


def server_streams(fms_server):
    '''
    Returns a dictionary with server streams:

    {'appInst': ['stream1', 'stream2']}
    '''
    streams = {}
    for key, appInst in fms_server.getActiveInstances()['data'].items():
        streams[appInst] = list(set(fms_server.getLiveStreams(appInst)['data'].values()))
    return streams

def m3u8_path(app, instance, event, stream):
    '''Returns the path where FMS servers the stream'''
    return '/hls-live/{app}/{instance}/{event}/{stream}.m3u8'.format(
        app=app,
        instance=instance,
        event=event,
        stream=stream,
    )
