# CocoTB. Base TestBench class

import logging
from typing import Any

from cocotb.log import SimLog
from cocotb_coverage.coverage import coverage_section, coverage_db, CoverItem, CoverPoint, CoverCross
from cocotb_util.cocotb_transaction import Transaction

from cocotb_util.cocotb_util import timeout, static_vars


class CoverProcessor(object):

    def __init__(
            self,
            name: str = "cocotb.coverage",
            report_cfg: dict = {'status': {}, 'final': {'bins': True}},
            **kwargs):

        self.log = SimLog(name)
        self.log.setLevel(logging.INFO)

        # Create coverage_section decorator with cover items. To be used for coverage collection.
        self.define()

        # setup cover results reporitng
        assert isinstance(report_cfg, dict)
        self.coverage_report_setup(report_cfg)

    def _post_process_dec(self, func):
        """ Coverage 'post_process' decorator. Call after all the Cover items.
        """
        def inner(*args, **kwargs):
            self._post_process()
            return func(*args, **kwargs)
        return inner

    def _post_process(self, *args, **kwargs):
        """Run 'post process' after all the cover data will be updated"""
        self.log.debug('System post process')
        self._update_covered_bins()

    def user_post_process(self, *args, **kwargs):
        """User post process func. May be overridden"""
        self.log.debug('User post process')

    def _update_covered_bins(self):
        """For every Cover (Point or Cross) create a list of covered bins and update it at every sample"""
        for cov_name, cov_item in coverage_db.items():
            self.log.debug(f"{cov_name} - {cov_item}")
            if isinstance(cov_item, CoverPoint):
                # create CoverItem.covered_bins attr
                try:
                    covered_bins = cov_item.covered_bins
                except AttributeError:
                    cov_item.covered_bins = []
                    covered_bins = cov_item.covered_bins
                # update covered bins
                for hit in cov_item.new_hits:
                    if cov_item.detailed_coverage[hit] == cov_item._at_least:
                        covered_bins.append(hit)
                        self.log.debug(f"Covered bins: {covered_bins}")
            elif isinstance(cov_item, CoverCross):
                # create CoverItem.covered_bins attr
                try:
                    covered_bins = cov_item.covered_bins
                except AttributeError:
                    cov_item.covered_bins = {}
                    for cp_name in cov_item._items:
                        cov_item.covered_bins[cp_name] = {'covered_bins': [], 'bin_cnt': {}}

                    # for every cp bin calc num of descendant ccp bins
                    for ccp_bin in cov_item.detailed_coverage:
                        for i, cp_bin in enumerate(ccp_bin):
                            cp_name = cov_item._items[i]
                            try:
                                cov_item.covered_bins[cp_name]['bin_cnt'][cp_bin] += 1
                            except KeyError:
                                cov_item.covered_bins[cp_name]['bin_cnt'][cp_bin] = 1
                    covered_bins = cov_item.covered_bins

                # update 'covered bins' for every ccp dimension
                for hit in cov_item.new_hits:
                    if cov_item.detailed_coverage[hit] == cov_item._at_least:
                        for i, cp_bin in enumerate(hit):
                            cp_name = cov_item._items[i]
                            covered_bins[cp_name]['bin_cnt'][cp_bin] -= 1
                            if covered_bins[cp_name]['bin_cnt'] == 0:
                                covered_bins[cp_name]['covered_bins'].append(cp_bin)
                                self.log.debug(f"Covered bins: {cp_name} - {covered_bins[cp_name]['covered_bins']}")

    def add_cover_items(self, *args):
        """Schedule Cover items (Point & Cross) and 'post_process()' calls"""
        self._coverage_section = coverage_section(*args, self._post_process_dec)

    def define(self):
        """Create coverage collector decorator using self.add_cover_items(CoverPoint, CoverCross, ...). To be overridden."""
        self.log.error('Not implemented')

    @timeout
    def collect(
            self,
            trx: Transaction,
            post_process_en: bool = False,
            report_en: bool = True):
        """Function to collect coverage. It makes sense to call it somewhere."""
        assert isinstance(trx, Transaction)

        @self._coverage_section
        def foo(trx):
            pass

        foo(trx)
        if report_en:
            self.status_report()
        if post_process_en:
            self.user_post_process()

    def coverage_report_setup(self, _coverage_report_cfg):
        """Check report config consistency with given coverage db"""
        cover_item_fields_supported = ['at_least', 'weight', 'new_hits', 'size', 'coverage', 'cover_percentage', 'detailed_coverage']
        assert isinstance(_coverage_report_cfg, dict)
        self._coverage_report_cfg = _coverage_report_cfg
        status_cfg = self._coverage_report_cfg.get('status', None)
        if status_cfg is None:
            self.log.info('No coverage status reported.')
            self._coverage_report_cfg['status'] = {}
        else:
            assert isinstance(_coverage_report_cfg['status'], dict)
            for cov_item_name, cov_item_field_name in [item for item in status_cfg.items()]:
                assert isinstance(cov_item_name, str)
                assert type(cov_item_field_name) in [str, list]
                if isinstance(cov_item_field_name, str):
                    status_cfg[cov_item_name] = [cov_item_field_name]  # convert to list
                cov_item = coverage_db.get(cov_item_name, None)
                if cov_item is None:
                    self.log.warning(f'Wrong coverage_db item: {cov_item_name}.*')
                    del status_cfg[cov_item_name]
                    continue
                for cov_item_field_name in [item for item in status_cfg[cov_item_name]]:
                    if cov_item_field_name not in cover_item_fields_supported:
                        self.log.warning(f'Wrong coverage_db item field: {cov_item_name}.{cov_item_field_name}')
                        status_cfg[cov_item_name].remove(cov_item_field_name)

    def status_report(self):
        """Function to report intermediate coverage status during the test. May be overridden."""
        for cov_item_name, cov_item_field_names in self._coverage_report_cfg['status'].items():
            for cov_item_field_name in cov_item_field_names:
                cov_item_field_value = getattr(coverage_db[cov_item_name], cov_item_field_name)
                if isinstance(cov_item_field_value, float):
                    self.log.info(f"{cov_item_name}.{cov_item_field_name} = {cov_item_field_value:2.2f}")
                else:
                    self.log.info(f"{cov_item_name}.{cov_item_field_name} = {cov_item_field_value}")

    def final_report(self):
        """Function to report final coverage result at the end of the test. May be overridden"""
        self.log.info('Coverage final results')
        bins = self._coverage_report_cfg.get('final', {}).get('bins', True)
        assert isinstance(bins, bool)
        coverage_db.report_coverage(self.log.info, bins=bins)
