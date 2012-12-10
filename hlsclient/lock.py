import os
import time

from lockfile.linklockfile import LinkLockFile

class ExpiringLinkLockFile(LinkLockFile):
    def expired(self, tolerance):
        return self.lock_age > tolerance

    @property
    def lock_age(self):
        return time.time() - os.path.getmtime(self.lock_file)

    def update_lock(self):
        os.utime(self.lock_file, None)

    def release_if_locking(self):
        if self.i_am_locking():
            self.release()
