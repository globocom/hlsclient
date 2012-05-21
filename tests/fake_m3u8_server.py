from bottle import route, run, response
import bottle


M3U8_SERVER = 'http://localhost:8845'


@route('/<:re:.*>.ts')
def all_ts():
    return 'FAKE TS\n'

@route('/variant-playlist.m3u8')
def variant_playlist():
    response.set_header('Content-Type', 'application/vnd.apple.mpegurl')
    return '''\
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1, BANDWIDTH=1280000
{server}/low.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=7680000
{server}/high.m3u8
'''.format(server=M3U8_SERVER)


@route('/low.m3u8')
def low_playlist():
    response.set_header('Content-Type', 'application/vnd.apple.mpegurl')
    return '''\
#EXTM3U
#EXT-X-TARGETDURATION:200
#EXTINF:100,
{server}/low1.ts
#EXTINF:100,
{server}/low2.ts
#EXT-X-ENDLIST
'''.format(server=M3U8_SERVER)


@route('/high.m3u8')
def high_playlist():
    response.set_header('Content-Type', 'application/vnd.apple.mpegurl')
    return '''\
#EXTM3U
#EXT-X-TARGETDURATION:200
#EXTINF:100,
{server}/high1.ts
#EXTINF:100,
{server}/high2.ts
#EXT-X-ENDLIST
'''.format(server=M3U8_SERVER)


if __name__ == '__main__':    
    bottle.debug = True
    run(host='localhost', port=8845)
