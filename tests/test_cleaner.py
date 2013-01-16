import os.path
import time
import csv
from hlsclient.helpers import load_config, get_ignore_patterns
from hlsclient.cleaner import clean

SECONDS = 1

def test_should_remove_old_files(tmpdir):
    tmpdir = str(tmpdir)
    old_fnames = 'old1.ts old2.m3u8 old3.bin audioold1.aac audioold2.aac d.txt'.split()
    fresh_files = 'a.ts audioold2.aac b.ts c.ts'.split()
    create_old_files(tmpdir, old_fnames, 60 * SECONDS)
    create_fresh_files(tmpdir, fresh_files)

    clean(tmpdir, 50 * SECONDS, [])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert sorted(os.listdir(tmpdir)) == sorted(fresh_files + ['d.txt'])


def test_should_remove_old_files_and_directories(tmpdir):
    tmpdir = str(tmpdir)
    dir1 = os.path.join(tmpdir, 'dir1')
    old_fnames = 'old1.ts old2.ts old3.ts'.split()
    fresh_files = 'a.ts b.ts c.ts'.split()
    os.makedirs(dir1)

    create_old_files(tmpdir, old_fnames, 60 * SECONDS)
    create_fresh_files(tmpdir, fresh_files)

    os.utime(dir1, (time.time() - 60 * SECONDS, time.time() - 60 * SECONDS))

    clean(tmpdir, 50 * SECONDS, [])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert sorted(os.listdir(tmpdir)) == sorted(fresh_files)

def test_should_remove_files_in_subdirs(tmpdir):
    tmpdir = str(tmpdir)
    dir1 = os.path.join(tmpdir, 'dir1')
    old_fnames = 'old1.ts old2.ts old3.ts'.split()
    fresh_files = 'a.ts b.ts c.ts'.split()
    os.makedirs(dir1)

    create_old_files(dir1, old_fnames, 60 * SECONDS)
    create_fresh_files(dir1, fresh_files)

    os.utime(dir1, (time.time() - 60 * SECONDS, time.time() - 60 * SECONDS))

    clean(tmpdir, 50 * SECONDS, [])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert sorted(os.listdir(dir1)) == sorted(fresh_files)


def test_should_not_remove_directories_that_are_not_empty(tmpdir):
    tmpdir = str(tmpdir)
    dir1 = os.path.join(tmpdir, 'dir1')
    os.makedirs(dir1)
    os.utime(dir1, (time.time() - 60 * SECONDS, time.time() - 60 * SECONDS))
    create_fresh_files(dir1, ['a.ts'])

    clean(tmpdir, 50 * SECONDS, [])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert os.listdir(tmpdir) == ['dir1']
    assert os.listdir(dir1) == ['a.ts']

def test_should_remove_directories_that_are_empty(tmpdir):
    tmpdir = str(tmpdir)
    dir1 = os.path.join(tmpdir, 'dir1')
    dir2 = os.path.join(dir1, 'dir2')
    os.makedirs(dir2)
    os.utime(dir1, (time.time() - 60 * SECONDS, time.time() - 60 * SECONDS))
    os.utime(dir2, (time.time() - 60 * SECONDS, time.time() - 60 * SECONDS))

    create_fresh_files(dir1, ['a.ts'])

    clean(tmpdir, 50 * SECONDS, [])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert os.listdir(tmpdir) == ['dir1']
    assert os.listdir(dir1) == ['a.ts']


def test_ensure_removes_are_based_on_access_time(tmpdir):
    tmpdir = str(tmpdir)
    old_fnames = 'old1.ts old2.ts old3.ts'.split()
    fresh_files = 'a.ts b.ts c.ts'.split()
    create_old_files(tmpdir, old_fnames, 60 * SECONDS)
    create_fresh_files(tmpdir, fresh_files)

    with open(os.path.join(tmpdir, 'old1.ts')) as f:
        f.read()

    clean(tmpdir, 50 * SECONDS, [])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert sorted(os.listdir(tmpdir)) == sorted(fresh_files + ['old1.ts'])

def test_ensure_files_with_a_dot_prefix_should_not_be_erased(tmpdir):
    tmpdir = str(tmpdir)
    some_time_ago = time.time() - 60 * SECONDS
    old_fnames = 'old1.ts old2.ts old3.ts .should_not_be_erased.ts'.split()

    config = load_config()
    ignores = get_ignore_patterns(config)

    create_old_files(tmpdir, old_fnames, some_time_ago)

    clean(tmpdir, 50 * SECONDS, ignores)
    time.sleep(0.01) # sleep because clean runs in another thread

    assert os.listdir(tmpdir) ==  ['.should_not_be_erased.ts']

def test_should_not_erase_files_with_ops_prefix(tmpdir):
    tmpdir = str(tmpdir)
    some_time_ago = time.time() - 60 * SECONDS

    config = load_config()
    ignores = get_ignore_patterns(config)

    old_dir1 = os.path.join(tmpdir, 'need_to_be_erased')
    old_dir2 = os.path.join(tmpdir, 'opsdir1')
    os.makedirs(old_dir1)
    os.makedirs(old_dir2)
    create_old_files(tmpdir, ['ops_acesso_simultaneo.ts', 'ops_rsrs.ts'], some_time_ago)
    os.utime(old_dir1, (some_time_ago, some_time_ago))
    os.utime(old_dir2, (some_time_ago, some_time_ago))

    clean(tmpdir, 50 * SECONDS, ignores)
    time.sleep(0.01) # sleep because clean runs in another thread

    assert sorted(os.listdir(tmpdir)) == sorted(['ops_acesso_simultaneo.ts', 'ops_rsrs.ts', 'opsdir1'])

def test_should_be_possible_to_ignore_globs(tmpdir):
    tmpdir = str(tmpdir)
    some_time_ago = time.time() - 60 * SECONDS
    old_dir1 = os.path.join(tmpdir, 'ignoredir1')
    old_dir2 = os.path.join(tmpdir, 'ignoredir2')
    old_dir3 = os.path.join(tmpdir, 'notignored')
    os.makedirs(old_dir1)
    os.makedirs(old_dir2)
    os.makedirs(old_dir3)
    create_old_files(tmpdir, ['ignore.ts'], some_time_ago)
    os.utime(old_dir1, (some_time_ago, some_time_ago))
    os.utime(old_dir2, (some_time_ago, some_time_ago))
    os.utime(old_dir3, (some_time_ago, some_time_ago))

    clean(tmpdir, 50 * SECONDS, ["ignore*"])
    time.sleep(0.01) # sleep because clean runs in another thread

    assert sorted(os.listdir(tmpdir)) == sorted(['ignore.ts', 'ignoredir1', 'ignoredir2'])

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
