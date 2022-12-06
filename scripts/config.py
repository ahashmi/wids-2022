from pathlib import Path
import logging

PROJ_ROOT = Path(r'../')

paths = {
    'data': PROJ_ROOT / 'DATA',
    'docs': PROJ_ROOT / 'docs',
    'ref': PROJ_ROOT / 'ref',
    'site_data': PROJ_ROOT / 'docs/_data',
}

def config_log(logger_nm:str) -> None:
    # create logger with 'spam_application'
    logger = logging.getLogger(logger_nm)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(f'{logger_nm}.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)