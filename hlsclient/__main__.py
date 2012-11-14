import logging
import time

from lockfile import LockTimeout
from lock import ExpiringLinkLockFile

import helpers

from balancer import Balancer
from consumer import consume_from_balancer
from discover import discover_playlists, get_servers
from combine import combine_playlists
from cleaner import clean


def main():
    config = helpers.load_config()
    helpers.setup_logging(config)

    logging.debug('HLS CLIENT Started')
    destination = config.get('hlsclient', 'destination')
    clean_maxage = config.getint('hlsclient', 'clean_maxage')
    not_modified_tolerance = config.getint('hlsclient', 'not_modified_tolerance')
    encrypt = config.getboolean('hlsclient', 'encrypt')

    # ignore all comma separated wildcard names for `clean` call
    ignores = helpers.get_ignore_patterns(config)
    balancer = Balancer(not_modified_tolerance)

    lock_path = config.get('lock', 'path')
    lock_timeout = config.getint('lock', 'timeout')
    lock_expiration = config.getint('lock', 'expiration')
    lock = ExpiringLinkLockFile(lock_path)

    while True:
        try:
            if lock.i_am_locking():
                lock.update_lock()
                playlists = discover_playlists(config)
                combine_playlists(playlists, destination)
                paths = get_servers(playlists)
                balancer.update(paths)
                consume_from_balancer(balancer, playlists, destination, encrypt)
                clean(destination, clean_maxage, ignores)
            elif lock.is_locked() and lock.expired(tolerance=lock_expiration):
                logging.warning("Lock expired. Breaking it.")
                lock.break_lock()
            else:
                lock.acquire(timeout=lock_timeout)
        except LockTimeout:
            logging.debug("Unable to acquire lock")
        except Exception as e:
            logging.exception('An unknown error happened')
        except KeyboardInterrupt:
            logging.debug('Quitting...')
            lock.release()
            return
        time.sleep(0.1)

if __name__ == "__main__":
    main()
