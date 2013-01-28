import itertools
import logging
import os
import signal
import subprocess
import sys
import time

from hlsclient import helpers
from hlsclient.combine import combine_playlists, get_actions
from hlsclient.cleaner import clean
from hlsclient.discover import discover_playlists
from hlsclient.workers.playlist import PlaylistWorker


class MasterWorker(object):

    def __init__(self):
        self.config = helpers.load_config()
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
        self.stop()

    def run_forever(self):
        signal.signal(signal.SIGTERM, self.interrupted)
        while True:
            try:
                self.run()
            except KeyboardInterrupt:
                logging.debug('Quitting...')
                break
            except:
                logging.exception('An unknown error happened')
            time.sleep(0.1)
        self.stop()

    def run(self):
        playlists = discover_playlists(self.config)
        logging.info("Found the following playlists: %s" % playlists)
        combine_playlists(playlists, self.destination)

        for playlist, is_variant in self.get_stream_groups(playlists):
            worker = PlaylistWorker(playlist, is_variant)
            if not worker.other_is_running():
                logging.debug('No worker found for playlist %s, %s' % (playlist, worker.lock.path))
                self.start_worker_in_background(playlist, is_variant)
            else:
                logging.debug('Worker found for playlist %s, %s' % (playlist, worker.lock.path))

        clean(self.destination, self.clean_maxage, self.ignores)

    def get_stream_groups(self, playlists):
        combine_actions = get_actions(playlists, 'combine')
        combine_outputs = [action['output'] for action in combine_actions]
        combine_inputs = [action['input'] for action in combine_actions]
        combine_inputs_flat = list(itertools.chain(*combine_inputs))
        not_variant = playlists['streams'].keys()

        variant_playlists = [(p, True) for p in combine_outputs]
        single_playlists = [(p, False) for p in (set(not_variant) - set(combine_inputs_flat))]

        return variant_playlists + single_playlists

    def start_worker_in_background(self, playlist, is_variant):
        args = [sys.executable, '-m', 'hlsclient', playlist]
        if is_variant:
            args.append("IS_VARIANT")
        subprocess.Popen(args)

    def stop(self):
        sys.exit(0)