from lock import ExpiringLinkLockFile
import logging
import signal
import sys
import time


import helpers
from lockfile import LockTimeout

class Worker(object):
    def __init__(self):
        self.config = helpers.load_config()
        self.setup_lock()

    def setup(self):
        pass

    def lock_path(self):
        return self.config.get('lock', 'path')

    def run(self):
        raise NotImplementedError()

    def lost_lock(self):
        pass

    def interrupted(self, *args):
        logging.info('Interrupted. Releasing lock.')
        self.stop()

    def setup_lock(self):
        lock_path = self.lock_path()
        self.lock_timeout = self.config.getint('lock', 'timeout')
        self.lock_expiration = self.config.getint('lock', 'expiration')
        self.lock = ExpiringLinkLockFile(lock_path)

    def run_forever(self):
        self.setup()
        signal.signal(signal.SIGTERM, self.interrupted)
        while True:
            try:
                self.run_if_locking()
            except LockTimeout:
                logging.debug("Unable to acquire lock")
            except Exception as e:
                logging.exception('An unknown error happened')
            except KeyboardInterrupt:
                logging.debug('Quitting...')
                self.stop()
            time.sleep(0.1)

    def run_if_locking(self):
        if self.can_run():
            self.lock.update_lock()
            self.run()

    def can_run(self):
        if self.other_is_running():
            logging.warning("Someone else acquired the lock")
            self.lost_lock()
        elif not self.lock.is_locked():
            self.lock.acquire(timeout=self.lock_timeout)
        return self.lock.i_am_locking()

    def other_is_running(self):
        other = self.lock.is_locked() and not self.lock.i_am_locking()
        if other and self.lock.expired(tolerance=self.lock_expiration):
            logging.warning("Lock expired. Breaking it")
            self.lock.break_lock()
            return False
        return other

    def stop(self):
        try:
            self.lock.release_if_locking()
        finally:
            sys.exit(0)
