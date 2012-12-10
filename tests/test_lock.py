from lockfile import LockTimeout
import pytest
import time

from hlsclient.lock import ExpiringLinkLockFile

def test_can_acquire_lock(tmpdir):
    lock = ExpiringLinkLockFile(str(tmpdir))
    lock.acquire()
    assert lock.i_am_locking()

def test_cannot_acquire_lock_if_it_is_locked(tmpdir):
    lock = ExpiringLinkLockFile(str(tmpdir))
    lock.acquire()

    second_lock = ExpiringLinkLockFile(str(tmpdir))
    with pytest.raises(LockTimeout):
        second_lock.acquire(timeout=1)
    assert second_lock.is_locked()
    assert not second_lock.i_am_locking()

def test_lock_expires(tmpdir):
    lock = ExpiringLinkLockFile(str(tmpdir))
    lock.acquire()
    time.sleep(1)
    assert lock.expired(1)
    assert not lock.expired(2)

def test_lock_can_be_breaked(tmpdir):
    lock = ExpiringLinkLockFile(str(tmpdir))
    lock.unique_name +=  '_really_unique_name'
    lock.acquire()
    lock.break_lock()

    second_lock = ExpiringLinkLockFile(str(tmpdir))
    second_lock.unique_name +=  '_avoid_duplicated_lock_name'
    second_lock.acquire()
    assert second_lock.i_am_locking()
    assert not lock.i_am_locking()


def test_release_if_locking_unlocks(tmpdir):
    lock_name = str(tmpdir.join('lockfile'))

    lock = ExpiringLinkLockFile(lock_name)
    lock.unique_name +=  '_really_unique_name'
    lock.acquire()
    lock.release_if_locking()

    second_lock = ExpiringLinkLockFile(lock_name)
    second_lock.unique_name +=  '_avoid_duplicated_lock_name'
    second_lock.acquire(timeout=1)
    assert second_lock.is_locked()
    assert second_lock.i_am_locking()
    assert not lock.i_am_locking()
