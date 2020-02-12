import argparse


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


def convert_to_rid_list(records):
    return [record['@rid'] for record in records]
