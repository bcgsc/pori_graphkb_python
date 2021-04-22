import argparse
import logging
import re
from typing import Iterable, List

from .constants import AA_3to1_MAPPING
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


def convert_aa_3to1(three_letter_notation: str) -> str:
    """
    Convert an Input string from 3 letter AA notation to 1 letter AA notation
    """
    result = []

    if ':' in three_letter_notation:
        # do not include the feature/gene in replacements
        pos = three_letter_notation.index(':')
        result.append(three_letter_notation[: pos + 1])
        three_letter_notation = three_letter_notation[pos + 1 :]

    last_match_end = 0  # exclusive interval [ )

    for match in re.finditer(r'[A-Z][a-z][a-z]', three_letter_notation):
        # add the in-between string
        result.append(three_letter_notation[last_match_end : match.start()])
        text = three_letter_notation[match.start() : match.end()]
        result.append(AA_3to1_MAPPING.get(text, text))
        last_match_end = match.end()

    result.append(three_letter_notation[last_match_end:])
    return ''.join(result)
