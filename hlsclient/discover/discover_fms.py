def discover(config):
    '''
    Receives the extra configuration parameters from [discover] section

    Returns a dictionary with format:

      {'/path1.m3u8': ['server1', 'server2'],
       '/path2.m3u8': ['server3', 'server4', 'server5']}

    '''
    raise NotImplementedError

def server_m3u8_paths(fms_server):
    '''
    Returns a list of m3u8 paths in a server,
    assuming that event's names are equal to stream's.
    '''
    for appInst, streams in server_streams(fms_server).items():
        app, inst = appInst.split('/')
        for stream in streams:
            yield m3u8_path(app, inst, stream, stream)

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
