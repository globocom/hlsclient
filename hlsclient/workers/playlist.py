import datetime
import logging
import md5
import random

from hlsclient import helpers
from hlsclient.balancer import Balancer
from hlsclient.consumer import consume_from_balancer
from hlsclient.discover import discover_playlists, get_servers
from hlsclient.workers.base_worker import Worker

MAX_TTL_IN_SECONDS = 600

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
