# CocoTB. Base Transaction class

import logging
from typing import Iterable

from cocotb_coverage.crv import Randomized
from cocotb.log import SimLog

from cocotb_util import cocotb_util


class Transaction(Randomized):

    def __init__(self, items: Iterable = []):
        super().__init__()
        self.log = SimLog("cocotb.testbench")
        # self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(logging.INFO)

        self._items = items
        for item in self._items:
            setattr(self, item, None)

    @cocotb_util.timeout
    def randomize(self):
        super().randomize()

    def __repr__(self):
        """Transaction object items string representation"""
        foo = {item: getattr(self, item, None) for item in self._items}
        return f'{foo}'


if __name__ == "__main__":
    foo = Transaction()

    for _ in range(100):
        foo.randomize()
