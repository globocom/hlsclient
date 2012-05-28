import ConfigParser
import logging
import time
import hashlib
import os
from urllib2 import HTTPError

from balancer import Balancer
from discover import PlaylistDiscover
from consumer import consume, random_key

def load_config(path=None):
    if path is None:
        path = os.getenv('HLSCLIENT_CONFIG', 'config.ini')
    config = ConfigParser.RawConfigParser()
    with open(path) as f:
        config.readfp(f)
    return config

def setup_logging():
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def main():
    setup_logging()
    logging.debug('HLS CLIENT Started')

    config = load_config()
    destination = config.get('hlsclient', 'destination')
    logging.debug('Config loaded')

    balancer = Balancer()
    keys = {}

    while True:
        d = PlaylistDiscover(config)
        d.create_index_for_variant_playlists(destination)
        paths = d.playlist_paths

        logging.info(u'Discovered the following paths: %s' % paths.items())

        balancer.update(paths)

        for resource in balancer.actives:
            resource_path = str(resource)
            logging.debug('Consuming %s' % resource_path)
            if resource_path not in keys:
                key_name = "key_%s.bin" % hashlib.md5(resource_path).hexdigest()[:5]
                keys[resource_path] = random_key(key_name)
            try:
                modified = consume(resource_path, destination, keys[resource_path])
            except (HTTPError, IOError, OSError) as err:
                logging.warning(u'Notifying error for resource %s: %s' % (resource_path, err))
                balancer.notify_error(resource.server, resource.path)
            else:
                if modified:
                    logging.info('Notifying content modified: %s' % resource)
                    balancer.notify_modified(resource.server, resource.path)
                else:
                    logging.debug('Content not modified: %s' % resource)
        time.sleep(2)

if __name__ == "__main__":
    main()
