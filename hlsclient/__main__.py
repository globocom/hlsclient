import md5
import logging
import time
import os
import signal
import sys

from lockfile import LockTimeout
from lock import ExpiringLinkLockFile

import helpers

from balancer import Balancer
from consumer import consume_from_balancer
from discover import discover_playlists, get_servers
from combine import combine_playlists
from cleaner import clean
from worker import Worker

SIG_SENT = False


def start_worker_in_background(playlist):
    AFTER_FORK_DELAY = 0.1
    os.spawnl(os.P_NOWAIT, sys.executable, '-m', 'hlsclient', playlist)


def start_as_master():
    config = helpers.load_config()
    helpers.setup_logging(config, "master process")

    logging.debug('HLS CLIENT Started')
    destination = config.get('hlsclient', 'destination')

    # ignore all comma separated wildcard names for `clean` call
    clean_maxage = config.getint('hlsclient', 'clean_maxage')
    ignores = helpers.get_ignore_patterns(config)

    lock_path = config.get('lock', 'path')
    lock_timeout = config.getint('lock', 'timeout')
    lock_expiration = config.getint('lock', 'expiration')
    lock = ExpiringLinkLockFile(lock_path)

    os.setpgrp()
    def signal_handler(*args):
        try:
            logging.info('Interrupted. Releasing lock.')
            lock.release_if_locking()
            logging.info('Killing childs.')
            global SIG_SENT
            if not SIG_SENT:
                SIG_SENT = True
                os.killpg(0, signal.SIGTERM)
        finally:
            sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            if lock.i_am_locking():
                lock.update_lock()
                playlists = discover_playlists(config)
                logging.info("Found the following playlists: %s" % playlists)
                combine_playlists(playlists, destination)

                for stream, value in playlists['streams'].items():
                    playlist = value['input-path']
                    worker = PlaylistWorker(playlist)
                    if not worker.lock.is_locked():
                        start_worker_in_background(playlist)
                    else:
                        logging.debug('Worker found for playlist %s' % stream)

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
            signal_handler()
            return
        time.sleep(0.1)


class PlaylistWorker(Worker):
    def __init__(self, playlist):
        self.playlist = playlist
        super(PlaylistWorker, self).__init__()

    def lock_path(self):
        lock_path = super(PlaylistWorker, self).lock_path()
        return '{0}.{1}'.format(lock_path, self.worker_id())

    def worker_id(self):
        return md5.md5(self.playlist).hexdigest()

    def setup(self):
        logging.debug('HLS CLIENT Started for {}'.format(self.playlist))
        helpers.setup_logging(self.config, "worker for {}".format(self.playlist))
        self.destination = self.config.get('hlsclient', 'destination')
        self.encrypt = self.config.getboolean('hlsclient', 'encrypt')
        not_modified_tolerance = self.config.getint('hlsclient', 'not_modified_tolerance')
        self.balancer = Balancer(not_modified_tolerance)

    def run(self):
        playlists = discover_playlists(self.config)
        worker_playlists = self.filter_playlists_for_worker(playlists)
        if not worker_playlists:
            logging.warning("Playlist is not available anymore")
            self.stop()

        paths = get_servers(worker_playlists)
        self.balancer.update(paths)
        consume_from_balancer(self.balancer,
                              worker_playlists,
                              self.destination,
                              self.encrypt)

    def filter_playlists_for_worker(self, playlists):
        for stream, value in playlists['streams'].items():
            if value['input-path'] == self.playlist:
                return {"streams": {stream: value}}
        return {}

    def lost_lock(self):
        self.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        worker = PlaylistWorker(sys.argv[1])
        worker.run_forever()
    else:
        start_as_master()
