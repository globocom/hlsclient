import hashlib
import logging
import time
import csv

import helpers

from urllib2 import HTTPError

from balancer import Balancer
from consumer import consume
from discover import discover_playlist_paths_and_create_indexes
from cleaner import clean


def consume_from_balancer(balancer, destination, encrypt):
    for playlist_resource in balancer.actives:
        try:
            m3u8_uri = str(playlist_resource)
            modified = consume(m3u8_uri, destination, encrypt)
        except (HTTPError, IOError, OSError) as err:
            logging.warning(u'Notifying error for resource %s: %s' % (playlist_resource, err))
            balancer.notify_error(playlist_resource.server, playlist_resource.path)
        else:
            if modified:
                logging.info('Notifying content modified: %s' % playlist_resource)
                balancer.notify_modified(playlist_resource.server, playlist_resource.path)
            else:
                logging.debug('Content not modified: %s' % playlist_resource)

def main():
    config = helpers.load_config()
    helpers.setup_logging(config)

    logging.debug('HLS CLIENT Started')
    destination = config.get('hlsclient', 'destination')
    clean_maxage = int(config.get('hlsclient', 'clean_maxage'))
    encrypt = config.getboolean('hlsclient', 'encrypt')

    # ignore all comma separated wildcard names for `clean` call
    ignores = helpers.get_ignore_patterns(config)

    balancer = Balancer()

    while True:
        try:
            paths = discover_playlist_paths_and_create_indexes(config, destination)
            balancer.update(paths)
            consume_from_balancer(balancer, destination, encrypt)
            clean(destination, clean_maxage, ignores)
        except Exception as e:
            logging.exception('An unknown error happened')
        except KeyboardInterrupt:
            logging.debug('Quitting...')
            return
        time.sleep(0.1)

if __name__ == "__main__":
    main()
