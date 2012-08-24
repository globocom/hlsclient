import os
import csv
import logging
import ConfigParser
from logging.handlers import TimedRotatingFileHandler

def load_config(path=None):
    if path is None:
        path = os.getenv('HLSCLIENT_CONFIG', 'config.ini')
    config = ConfigParser.RawConfigParser()
    with open(path) as f:
        config.readfp(f)
    return config

def setup_logging(config):
    level = getattr(logging, config.get('hlsclient', 'log_level'))
    format = '%(asctime)s - %(levelname)s - %(message)s'
    try:
        filename = config.get('hlsclient', 'log_filename')
        handler = TimedRotatingFileHandler(filename, when='midnight', encoding='utf-8', interval=1)
    except ConfigParser.NoOptionError:
        handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter(format))

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

def get_ignore_patterns(config):
    if config.has_option('hlsclient', 'clean_ignore'):
        patterns = config.get('hlsclient', 'clean_ignore')
        ignore_patterns = list(csv.reader([patterns]))[0]
        return [ignore.strip() for ignore in ignore_patterns]

    return []


