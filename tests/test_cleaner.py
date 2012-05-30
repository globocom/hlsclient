import os.path
import time

from hlsclient.cleaner import clean

SECONDS = 1

def test_should_remove_old_files(tmpdir):
    tmpdir = str(tmpdir)
    old_fnames = 'old1.txt old2.txt old3.txt'.split()
    fresh_files = 'a.txt b.txt c.txt'.split()
    create_old_files(tmpdir, old_fnames, 60 * SECONDS)
    create_fresh_files(tmpdir, fresh_files)

    clean(tmpdir, 50 * SECONDS)
    assert os.listdir(tmpdir) == fresh_files


def test_should_remove_old_files_and_directories(tmpdir):
    tmpdir = str(tmpdir)
    nested_dir1 = os.path.join(tmpdir, 'dir1')
    nested_dir2 = os.path.join(nested_dir1, 'dir2')
    old_fnames = 'old1.txt old2.txt old3.txt'.split()
    fresh_files = 'a.txt b.txt c.txt'.split()
    os.makedirs(nested_dir2)

    create_old_files(nested_dir2, old_fnames, 60 * SECONDS)
    create_old_files(tmpdir, old_fnames, 60 * SECONDS)
    create_fresh_files(tmpdir, fresh_files)

    os.utime(nested_dir1, (time.time() - 60 * SECONDS, time.time() - 60 * SECONDS))

    clean(tmpdir, 50 * SECONDS)
    assert os.listdir(tmpdir) == fresh_files


def test_ensure_removes_are_based_on_access_time(tmpdir):
    tmpdir = str(tmpdir)
    old_fnames = 'old1.txt old2.txt old3.txt'.split()
    fresh_files = 'a.txt b.txt c.txt'.split()
    create_old_files(tmpdir, old_fnames, 60 * SECONDS)
    create_fresh_files(tmpdir, fresh_files)

    with open(os.path.join(tmpdir, 'old1.txt')) as f:
        f.read()

    clean(tmpdir, 50 * SECONDS)
    assert os.listdir(tmpdir) == fresh_files + ['old1.txt']


def create_old_files(destination, files, modification_timedelta):
    create_dummy_files(destination, files, mtime=time.time() - modification_timedelta)

def create_fresh_files(destination, files):
    create_dummy_files(destination, files, mtime=time.time())

def create_dummy_files(destination, files, mtime):
    for fname in files:
        fpath = os.path.join(destination, fname)
        with open(fpath, 'w') as f:
            f.write('dummy file')
        os.utime(fpath, (mtime, mtime))
