# CocoTB. Base Transaction class

import logging
from typing import Iterable
import json
import os
import os.path as osp

from cocotb_coverage.crv import Randomized
from cocotb.log import SimLog

from cocotb_util import cocotb_util


class Transaction(Randomized):

    def __init__(
            self,
            items: Iterable = [],
            store_trx: bool = False,  # flag to store trx to file ('errornous' or 'on request')
            store_trx_fname: str = 'store_trx.txt',  # file name to store trx
            reset_store_trx_file: bool = True):  # flag to remove trx stored at previous run
        super().__init__()
        self.log = SimLog("cocotb.testbench.trx")
        # self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(logging.INFO)

        self._items = items
        for item in self._items:
            setattr(self, item, None)

        self._load_from_file_gen = None

        self.store_trx = store_trx
        self.store_trx_fname = store_trx_fname
        if reset_store_trx_file:
            if osp.isfile(self.store_trx_fname):
                os.remove(self.store_trx_fname)

    def __repr__(self):
        """Transaction object items string representation"""
        foo = {item: getattr(self, item, None) for item in self._items}
        return f'{foo}'

    def randomize(self):
        super().randomize()

    def post_randomize(self):
        """To be overridden"""
        self.log.debug('Not implemented')
        # self.load_from_file()

    def load_from_file(self, fname=None):
        """Load trx content from file"""
        fname = self.store_trx_fname if fname is None else fname

        def load_from_file_gen():
            with open(fname, 'r') as fid:
                for trx_str in fid.readlines():
                    yield json.loads(trx_str)

        # create 'trx from file' generator
        if self._load_from_file_gen is None:
            self._load_from_file_gen = load_from_file_gen()

        # overwrite trx using 'data from file'
        try:
            trx = next(self._load_from_file_gen)
        except StopIteration:
            self.log.warning(f'Trx from file are over')
        else:
            for item in trx:
                setattr(self, item, trx[item])
            self.log.info(f'Trx content was overwritten from file: {repr(self)}')

    def store_to_file(self, store_trx=None, fname=None):
        """Store trx item to file. """
        store_trx = self.store_trx if store_trx is None else store_trx
        if store_trx:
            trx = {item: getattr(self, item, None) for item in self._items}
            fname = self.store_trx_fname if fname is None else fname
            with open(fname, 'a') as fid:
                trx_str = json.dumps(trx)
                fid.write(f"{trx_str}\n")


if __name__ == "__main__":
    foo = Transaction()

    for _ in range(100):
        foo.randomize()
