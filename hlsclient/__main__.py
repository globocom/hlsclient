import logging
import time

import helpers

from balancer import Balancer
from consumer import consume_from_balancer
from discover import discover_playlists, get_paths
from combine import combine_playlists
from cleaner import clean


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
            playlists = discover_playlists(config)
            combine_playlists(playlists, destination)
            paths = get_paths(playlists)
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
