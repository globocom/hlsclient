import os
import time
import random

from lockfile.linklockfile import LinkLockFile

class ExpiringLinkLockFile(LinkLockFile):
    def __init__(self, *args, **kwargs):
        LinkLockFile.__init__(self, *args, **kwargs)
        self.unique_name = "{original_name}_{base_path}_{random}.lock".format(
            original_name=self.unique_name,
            base_path=os.path.basename(self.path),
            random="%0x" % random.randint(0, 2**64))

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
