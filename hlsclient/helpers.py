import os
import logging
import ConfigParser

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

