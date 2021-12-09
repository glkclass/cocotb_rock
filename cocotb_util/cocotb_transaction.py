# CocoTB. Base Transaction class

import logging as log
from typing import Iterable

class Transaction(object):

    def __init__(self, items: Iterable = []):
        self.log = log.getLogger()
        self.log.setLevel(log.INFO)
        self._items = items
        for item in self._items:
            setattr(self, item, None)

    def __repr__(self):
        """Transaction object items string representation"""
        foo = {item: getattr(self, item, None) for item in self._items}
        return f'{foo}'

    def randomize(self):
        """Assign random values to Transaction items. To be overridden."""
        return self
