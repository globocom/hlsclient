import atexit
import md5
import logging
import time
import os
import signal
import sys
import subprocess

from lockfile import LockTimeout
from lock import ExpiringLinkLockFile

import helpers

from balancer import Balancer
from consumer import consume_from_balancer
from discover import discover_playlists, get_servers
from combine import combine_playlists
from cleaner import clean


def worker_started(playlist, config):
    lock_path = lock_path_for(config, playlist)
    lock_expiration = config.getint('lock', 'expiration')
    lock = ExpiringLinkLockFile(lock_path)

    if lock.is_locked() and lock.expired(tolerance=lock_expiration):
        logging.warning("Lock for playlist {playlist} expired. Breaking it.".format(playlist=playlist))
        lock.break_lock()

    return lock.is_locked()

def worker_id(playlist):
    return md5.md5(playlist).hexdigest()

def start_worker_in_background(playlist):
    AFTER_FORK_DELAY = 0.1
    os.spawnv(os.P_NOWAIT, sys.executable, ['-m', 'hlsclient', playlist])
    # delay because fork() seems to limit how many forks
    # can be created in a time window
    time.sleep(AFTER_FORK_DELAY)

def find_worker_playlists(current_playlist, playlists):
    for stream, value in playlists['streams'].items():
        if value['input-path'] == current_playlist:
            return {"streams": {stream: value}}
    return {}

def save_server_name(playlists):
    pass


def lock_path_for(config, current_playlist):
    return '{0}.{1}'.format(config.get('lock', 'path'), worker_id(current_playlist))



def start_as_master():
    config = helpers.load_config()
    helpers.setup_logging(config, "master process")

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

    def signal_handler(signal, frame):
        try:
            logging.info('Interrupted. Releasing lock.')
            lock.release_if_locking()
        finally:
            sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            if lock.i_am_locking():
                lock.update_lock()
                playlists = discover_playlists(config)

                combine_playlists(playlists, destination)
                for stream, value in playlists['streams'].items():
                    playlist = value['input-path']
                    if not worker_started(playlist, config):
                        start_worker_in_background(playlist)
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
            lock.release_if_locking()
            return
        time.sleep(0.1)


def run_worker_task(config, current_playlist, destination, balancer, encrypt):
    playlists = discover_playlists(config)

    worker_playlists = find_worker_playlists(current_playlist, playlists)
    if not worker_playlists:
        return False

    paths = get_servers(worker_playlists)
    balancer.update(paths)
    # save_server_name(worker_playlists)
    consume_from_balancer(balancer, worker_playlists, destination, encrypt)
    return True


def start_as_worker(current_playlist):
    config = helpers.load_config()
    helpers.setup_logging(config, "worker for {}".format(current_playlist))

    logging.debug('HLS CLIENT Started for {}'.format(current_playlist))
    destination = config.get('hlsclient', 'destination')
    clean_maxage = config.getint('hlsclient', 'clean_maxage')
    not_modified_tolerance = config.getint('hlsclient', 'not_modified_tolerance')
    encrypt = config.getboolean('hlsclient', 'encrypt')

    # ignore all comma separated wildcard names for `clean` call
    ignores = helpers.get_ignore_patterns(config)
    balancer = Balancer(not_modified_tolerance)



    balancer = Balancer(not_modified_tolerance)

    lock_path = lock_path_for(config, current_playlist)
    lock_timeout = config.getint('lock', 'timeout')
    lock_expiration = config.getint('lock', 'expiration')
    lock = ExpiringLinkLockFile(lock_path)

    @atexit.register
    def release_lock(*args):
        try:
            logging.info('Interrupted. Releasing lock.')
            lock.release_if_locking()
        finally:
            sys.exit(0)

    while True:
        try:
            if lock.i_am_locking():
                lock.update_lock()
                if not run_worker_task(config, current_playlist, destination, balancer, encrypt):
                    return
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
            lock.release_if_locking()
            return
        time.sleep(0.1)





if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_as_worker(sys.argv[1])
    else:
        start_as_master()
