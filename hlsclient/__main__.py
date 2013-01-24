import datetime
import logging
import md5
import os
import random
import signal
import sys


import helpers
from balancer import Balancer
from consumer import consume_from_balancer
from combine import combine_playlists
from cleaner import clean
from discover import discover_playlists, get_servers
from worker import Worker

MAX_TTL_IN_SECONDS = 600

class MasterWorker(Worker):
    def setup(self):
        self.sig_sent = False
        helpers.setup_logging(self.config, "master process")
        logging.debug('HLS CLIENT Started')
        self.destination = self.config.get('hlsclient', 'destination')

        # ignore all comma separated wildcard names for `clean` call
        self.clean_maxage = self.config.getint('hlsclient', 'clean_maxage')
        self.ignores = helpers.get_ignore_patterns(self.config)

        # Setup process group, so we can kill the childs
        os.setpgrp()

    def interrupted(self, *args):
        if not self.sig_sent:
            self.sig_sent = True
            os.killpg(0, signal.SIGTERM)
        super(MasterWorker, self).interrupted(*args)

    def run(self):
        playlists = discover_playlists(self.config)
        logging.info("Found the following playlists: %s" % playlists)
        combine_playlists(playlists, self.destination)

        for stream, value in playlists['streams'].items():
            playlist = value['input-path']
            worker = PlaylistWorker(playlist)
            if not worker.other_is_running():
                logging.debug('No worker found for playlist %s' % playlist)
                self.start_worker_in_background(playlist)
            else:
                logging.debug('Worker found for playlist %s' % playlist)

        clean(self.destination, self.clean_maxage, self.ignores)

    def start_worker_in_background(self, playlist):
        os.spawnl(os.P_NOWAIT, sys.executable, '-m', 'hlsclient', playlist)


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
        helpers.setup_logging(self.config, "worker for {}".format(self.playlist))
        logging.debug('HLS CLIENT Started for {}'.format(self.playlist))

        self.destination = self.config.get('hlsclient', 'destination')
        self.encrypt = self.config.getboolean('hlsclient', 'encrypt')
        not_modified_tolerance = self.config.getint('hlsclient', 'not_modified_tolerance')
        self.balancer = Balancer(not_modified_tolerance)

        ttl = datetime.timedelta(seconds=random.randint(1, MAX_TTL_IN_SECONDS))
        self.death_time = datetime.datetime.now() + ttl

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

    def should_run(self):
        should_live = datetime.datetime.now() < self.death_time
        if not should_live:
            logging.info("Worker {} should die now!".format(self.worker_id()))
        return should_live

    def lost_lock_callback(self):
        self.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        worker = PlaylistWorker(sys.argv[1])
        worker.run_forever()
    else:
        master = MasterWorker()
        master.run_forever()
