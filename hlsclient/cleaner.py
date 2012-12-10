import os
import time
import shutil
import logging
import re
import fnmatch


FILES_PATTERN = re.compile('.+\.(ts|m3u8|aac|bin)$')

def path_age(path):
    atime = os.path.getatime(path)
    mtime = os.path.getmtime(path)
    return time.time() - max(atime, mtime)

def filter_old_paths(basepath, paths, maxage):
    for path in paths:
        fullpath = os.path.join(basepath, path)
        if os.path.exists(fullpath) and path_age(fullpath) > maxage:
            yield fullpath

def filter_old_files(basepath, paths, maxage):
    old_paths = filter_old_paths(basepath, paths, maxage)
    return (f for f in old_paths if FILES_PATTERN.match(f))

def filter_ignored(names, ignores):
    # we filter the list in place so os.walk will not look in subdirs of ignored paths
    for name in names[:]:
        if any(fnmatch.fnmatch(name, ignore) for ignore in ignores):
            names.remove(name)
    return names

def clean(path, maxage, ignores):
    logging.debug("Cleaning {path} (maxage = {maxage}s)".format(path=path, maxage=maxage))
    for root, dirs, files in os.walk(path):

        files = filter_ignored(files, ignores)
        for filename in filter_old_files(root, files, maxage):
            logging.debug("Removing old file {path}".format(path=filename))
            os.remove(filename)

        dirs = filter_ignored(dirs, ignores)
        for directory in filter_old_paths(root, dirs, maxage):
            if os.listdir(directory) == []:
                logging.debug("Removing old directory {path}".format(path=directory))
                os.rmdir(directory)
