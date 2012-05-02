import m3u8

def consume(m3u8_path, destination_path):
	"Receives a m3u8 path and copies all files to a local path"
	playlist = m3u8.M3U8()
	playlist.load(m3u8_path)