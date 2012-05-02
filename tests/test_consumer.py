import m3u8
from hlsclient.consumer import consume


def test_consume_loads_path(monkeypatch):
	called_args = []
	class FakeM3U8(object):
		def load(self, url):
			called_args.append(url)

	monkeypatch.setattr(m3u8, 'M3U8', FakeM3U8)
	consume('uri', '/path')
	assert ['uri'] == called_args
