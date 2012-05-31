import os
import time
import shutil
import logging
import re


FILES_PATTERN = re.compile('.+\.(ts|m3u8|bin)$')

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

def clean(path, maxage):
    logging.debug("Cleaning {path} (maxage = {maxage}s)".format(path=path, maxage=maxage))
    for root, dirs, files in os.walk(path):
        for filename in filter_old_files(root, files, maxage):
            logging.debug("Removing old file {path}".format(path=filename))
            os.remove(filename)
        for directory in filter_old_paths(root, dirs, maxage):
            logging.debug("Removing old directory {path}".format(path=directory))
            shutil.rmtree(directory)