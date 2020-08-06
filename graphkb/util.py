import argparse
import logging
import re
from typing import Iterable, List

from .types import Record

# name the logger after the package to make it simple to disable for packages using this one as a dependency
# https://stackoverflow.com/questions/11029717/how-do-i-disable-log-messages-from-the-requests-library
VERBOSE_ERROR_CODE = (logging.INFO + logging.DEBUG) // 2
logging.addLevelName(VERBOSE_ERROR_CODE, 'VERBOSE')
logger = logging.getLogger('graphkb')
# add shortbut for verbose logging
setattr(logger, 'verbose', lambda *pos, **kw: logger.log(VERBOSE_ERROR_CODE, *pos, **kw))
LOG_LEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warn': logging.WARN,
    'error': logging.ERROR,
    'verbose': VERBOSE_ERROR_CODE,
}


class IterableNamespace(argparse.Namespace):
    def __init__(self, *pos, **kwargs):
        argparse.Namespace.__init__(self, *pos, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def __getitem__(self, key):
        return getattr(self, key)


def convert_to_rid_list(records: Iterable[Record]) -> List[str]:
    """
    Given a list of records, return their record IDs
    """
    return [record['@rid'] for record in records]


class FeatureNotFoundError(Exception):
    pass


def looks_like_rid(rid: str) -> bool:
    """
    Check if an input string looks like a GraphKB ID
    """
    if re.match(r'^#-?\d+:-?\d+$', rid):
        return True
    return False
