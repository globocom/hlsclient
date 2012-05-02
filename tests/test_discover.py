import ConfigParser
import io

from hlsclient.discover import discover
import hlsclient.discover.discover_fms

def test_discover_uses_the_correct_backend(monkeypatch):
    sample_config = """[discover]
backend = hlsclient.discover.discover_fms
port = 1111
user = user
password = password
servers = backend1.globoi.com
          backend2.globoi.com
          backend3.globoi.com
"""
    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(sample_config))
    FAKE_RESPONSE = {'/path': ['server']}
    called_args = []
    def fake_discover_fms(config):
        called_args.append(config)
        return FAKE_RESPONSE

    monkeypatch.setattr(hlsclient.discover.discover_fms, 'discover',
        fake_discover_fms)
    assert FAKE_RESPONSE == discover(config)
    assert [config] == called_args
