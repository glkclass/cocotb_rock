# CocoTB. Base TestBench class

import logging
from typing import Any

from cocotb.log import SimLog
from cocotb_coverage.coverage import coverage_section, coverage_db

from cocotb_util.cocotb_agent import BusAgent
from cocotb_util.cocotb_scoreboard import Scoreboard
from cocotb_util.cocotb_transaction import Transaction


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

    def init(self):
        """Init TestBench before test started. To be overridden if needed."""
        pass

    def coverage_define(self):
        """Create and return coverage collector. To be overridden if needed."""
        return coverage_section()

    def coverage_collect(self, trx):
        """Function to collect coverage. Should be called somewhere. If needed."""
        @self.coverage_section
        def foo(trx):
            pass
        foo(trx)
        self.report_coverage_status()

    def report_coverage(self):
        """Function to report final coverage result. Maybe overridden if needed"""
        self.log.info('Coverage final results')
        coverage_db.report_coverage(self.log.info, bins=True)

    def report_coverage_status(self):
        """Function to report intermediate coverage status. Maybe overridden if needed"""
        coverage_db.report_coverage(self.log.info)

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
        self.report_coverage()
        raise self.scoreboard.result
