import argparse
from typing import Iterable, Sequence

from .types import Record


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


def convert_to_rid_list(records: Iterable[Record]) -> Sequence[str]:
    """
    Given a list of records, return their record IDs
    """
    return [record['@rid'] for record in records]


class FeatureNotFoundError(Exception):
    pass
