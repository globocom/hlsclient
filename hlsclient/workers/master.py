import logging
import os
import signal
import subprocess
import sys


from hlsclient import helpers
from hlsclient.combine import combine_playlists
from hlsclient.cleaner import clean
from hlsclient.discover import discover_playlists
from hlsclient.workers.base_worker import Worker
from hlsclient.workers.playlist import PlaylistWorker


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
                logging.debug('No worker found for playlist %s, %s' % (playlist, worker.lock.path))
                self.start_worker_in_background(playlist)
            else:
                logging.debug('Worker found for playlist %s, %s' % (playlist, worker.lock.path))

        clean(self.destination, self.clean_maxage, self.ignores)

    def start_worker_in_background(self, playlist):
        subprocess.Popen([sys.executable, '-m', 'hlsclient', playlist])
