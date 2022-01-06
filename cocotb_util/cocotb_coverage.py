# CocoTB. Base TestBench class

import logging
from functools import wraps

from cocotb.log import SimLog
from cocotb_coverage.coverage import coverage_db

from cocotb_coverage.coverage import CoverPoint as CocoTBCoverPoint
from cocotb_coverage.coverage import CoverCross as CocoTBCoverCross


class CoverPoint(CocoTBCoverPoint):
    def __new__(cls, name, *args, **kwargs):
        if name in coverage_db:
            return coverage_db[name]
        else:
            return super().__new__(cls, name)

    def __init__(self, name, *args, inj=False, **kwargs):
        if name not in coverage_db:
            super().__init__(name, *args, inj=inj, **kwargs)
            if getattr(self, 'log', None) is None:
                self.log = SimLog(f"cocotb.{name}")
                self.log.setLevel(logging.INFO)
            self._covered_bins = []  # to fill with covered bins

    def __call__(self, f):
        """Collect coverage decorator. Call super func + custom func"""
        super_call = super().__call__(f)

        @wraps(f)
        def _wrapped_function(*cb_args, **cb_kwargs):
            foo = super_call(*cb_args, **cb_kwargs)
            self.update_covered_bins()
            return foo
        return _wrapped_function

    def update_covered_bins(self):
        """Update list of covered bins"""
        for hit in self.new_hits:
            if self.detailed_coverage[hit] == self._at_least:
                self._covered_bins.append(hit)
                self.log.warning(f"Covered bins: {self._covered_bins}")

    @property
    def covered_bins(self):
        try:
            return self._covered_bins
        except AttributeError:
            return None

    @property
    def bin_cnt(self):
        try:
            return self._bin_cnt
        except AttributeError:
            return None


class CoverCross(CocoTBCoverCross):

    def __new__(cls, name, *args, **kwargs):
        if name in coverage_db:
            return coverage_db[name]
        else:
            return super().__new__(cls, name)

    def __init__(self, name, *args, **kwargs):
        if name not in coverage_db:
            super().__init__(name, *args, **kwargs)
            if getattr(self, 'log', None) is None:
                self.log = SimLog(f"cocotb.{name}")
                self.log.setLevel(logging.INFO)

            # to calc covered cp bins for every ccp dimension
            self._covered_bins = {}
            self._bin_cnt = {}
            for cp_name in self._items:
                self._covered_bins[cp_name] = []  # to fill with covered bins
                self._bin_cnt[cp_name] = {}  # for every cp prepare dict with {cp_bin: num_child_ccp_bins}
            # for every cp bin calc num of descendant ccp bins
            for ccp_bin in self.detailed_coverage:
                for i, cp_bin in enumerate(ccp_bin):
                    cp_name = self._items[i]
                    try:
                        self._bin_cnt[cp_name][cp_bin] += 1
                    except KeyError:
                        self._bin_cnt[cp_name][cp_bin] = 1

    def __call__(self, f):
        super_call = super().__call__(f)

        @wraps(f)
        def _wrapped_function(*cb_args, **cb_kwargs):
            foo = super_call(*cb_args, **cb_kwargs)
            self.update_covered_bins()
            return foo
        return _wrapped_function

    def update_covered_bins(self):
        """Update list of covered cp bins for every ccp dimension"""
        # Update 'covered bins' for every ccp dimension
        for hit in self.new_hits:
            if self.detailed_coverage[hit] == self._at_least:
                for i, cp_bin in enumerate(hit):
                    cp_name = self._items[i]
                    self._bin_cnt[cp_name][cp_bin] -= 1
                    if self._bin_cnt[cp_name][cp_bin] == 0:
                        self._covered_bins[cp_name].append(cp_bin)
                        self.log.warning(f"Covered bins: {cp_name} - {self._covered_bins[cp_name]}")

    @property
    def covered_bins(self):
        try:
            return self._covered_bins
        except AttributeError:
            return None

    @property
    def bin_cnt(self):
        try:
            return self._bin_cnt
        except AttributeError:
            return None
