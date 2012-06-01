import hashlib
import logging
import time

import helpers

from logging.handlers import TimedRotatingFileHandler
from urllib2 import HTTPError

from balancer import Balancer
from consumer import consume, KeyManager
from discover import PlaylistDiscover
from cleaner import clean


def main():
    config = helpers.load_config()
    helpers.setup_logging(config)

    logging.debug('HLS CLIENT Started')
    destination = config.get('hlsclient', 'destination')
    clean_maxage = int(config.get('hlsclient', 'clean_maxage'))

    balancer = Balancer()
    key_manager = KeyManager()

    while True:
        d = PlaylistDiscover(config)
        d.create_index_for_variant_playlists(destination)
        paths = d.playlist_paths

        logging.info(u'Discovered the following paths: %s' % paths.items())

        balancer.update(paths)

        for resource in balancer.actives:
            resource_path = str(resource)
            logging.debug('Consuming %s' % resource_path)
            if resource_path not in key_manager.keys:
                key_name = "key_%s.bin" % hashlib.md5(resource_path).hexdigest()[:5]
                key_manager.keys[resource_path] = key_manager.get_key(key_name)
            try:
                modified = consume(resource_path, destination, key_manager.keys[resource_path])
            except (HTTPError, IOError, OSError) as err:
                logging.warning(u'Notifying error for resource %s: %s' % (resource_path, err))
                balancer.notify_error(resource.server, resource.path)
            else:
                if modified:
                    logging.info('Notifying content modified: %s' % resource)
                    balancer.notify_modified(resource.server, resource.path)
                else:
                    logging.debug('Content not modified: %s' % resource)
        clean(destination, clean_maxage)
        time.sleep(2)

if __name__ == "__main__":
    main()
