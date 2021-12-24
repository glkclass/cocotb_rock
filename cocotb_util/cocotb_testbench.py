# CocoTB. Base TestBench class

import logging
from typing import Any

from cocotb.log import SimLog
from cocotb_coverage.coverage import coverage_section, coverage_db

from cocotb_util.cocotb_agent import BusAgent
from cocotb_util.cocotb_scoreboard import Scoreboard
from cocotb_util.cocotb_transaction import Transaction
from cocotb_util.cocotb_util import timeout


class TestBench(object):

    def __init__(
        self,
        agent: BusAgent = None,
        scoreboard: Scoreboard = None,
        **kwargs: Any
    ):
        self.log = SimLog("cocotb.testbench")
        self.log.setLevel(logging.INFO)

        self.agent = agent
        self.scoreboard = scoreboard
        self.runs = 0
        self.max_runs = 1

        # run optional initialization
        self.init()

        # create coverage_section decorator to be used for coverage collection
        self.coverage_section = self.coverage_define()

        self.coverage_report_cfg = {
            'status': {None: None},
            'final': {'bins': True}
        }

    def init(self):
        """Init TestBench before test started. To be overridden if needed."""
        pass

    def coverage_define(self):
        """Create and return coverage collector. To be overridden if needed."""
        return coverage_section()

    @timeout
    def coverage_collect(self, trx):
        """Function to collect coverage. Should be called somewhere. If needed."""
        @self.coverage_section
        def foo(trx):
            pass
        foo(trx)
        self.report_coverage_status()

    def set_coverage_report(self, coverage_report_cfg):
        self.coverage_report_cfg = coverage_report_cfg
        status_cfg = self.coverage_report_cfg.get('status', None)
        if status_cfg is None:
            self.log.info('No coverage status reported.')
            self.coverage_report_cfg['status'] = {}
        else:
            wrong_items = []
            for item in status_cfg:
                cov_item = coverage_db.get(item, None)
                cov_item_field = getattr(cov_item, status_cfg[item], None)
                if cov_item is None or cov_item_field is None:
                    self.log.warning(f'Wrong coverage_db address: {item}:{status_cfg[item]}')
                    wrong_items.append(item)
            for item in wrong_items:
                del status_cfg[item]

    def report_coverage_status(self):
        """Function to report intermediate coverage status. Maybe overridden if needed"""
        for item in self.coverage_report_cfg['status']:
            self.log.info(f"{item}.{self.coverage_report_cfg['status'][item]} = {getattr(coverage_db[item], self.coverage_report_cfg['status'][item]):2.2f}")

    def report_coverage_final(self):
        """Function to report final coverage result. Maybe overridden if needed"""
        self.log.info('Coverage final results')
        coverage_db.report_coverage(self.log.info, bins=self.coverage_report_cfg.get('final', {}).get('bins', True))

    async def run(self):
        """Run tests cases. To be overridden."""
        for trx in self.sequencer(Transaction):
            if self.agent.monitor is not None:
                self.agent.monitor.add_expected(trx)
            if self.agent.driver is not None:
                self.coverage_collect(trx)
                await self.agent.driver.send(trx)

    def check(self):
        """Check run statistics after test finished. To be overridden if needed."""
        pass

    def test_goal_achieved(self):
        """Stop testing when test goal achieved. To be overridden."""
        return self.runs >= self.max_runs

    def sequencer(self, Trx: Transaction, *args):
        """Generate randomized Trx while goal not achieved"""
        trx = Trx(*args)
        while not self.test_goal_achieved():
            self.log.info(f'Test case # {self.runs}')
            trx.randomize()
            yield trx
            self.runs += 1

    async def run_tb(self):
        """Run test cases."""
        await self.run()
        self.log.info(f'Finish tests. {self.runs} transactions were run.')
        self.report_coverage_final()
        raise self.scoreboard.result
