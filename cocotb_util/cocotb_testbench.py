# CocoTB. Base TestBench class

import logging
from typing import Any, Callable

from cocotb.log import SimLog
from cocotb_coverage.coverage import coverage_section, coverage_db

from cocotb_util.cocotb_agent import BusAgent
from cocotb_util.cocotb_scoreboard import Scoreboard
from cocotb_util.cocotb_transaction import Transaction
from cocotb_util.cocotb_coverage_processor import CoverProcessor
from cocotb_util.cocotb_util import timeout, static_vars


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

        # self.agent = BusAgent()
        # self.scoreboard = ScoreBoard()
        # self.coverage = CoverProcessor()

    def init(self):
        """Init TestBench before test started. To be overridden if needed."""
        pass

    async def run(self):
        """Run tests cases. To be overridden."""
        for trx in self.sequencer(Transaction, self.stop()):
            if self.agent.monitor is not None:
                self.agent.monitor.add_expected(trx)
            if self.agent.driver is not None:
                await self.agent.driver.send(trx)
            self.coverage.collect(trx)

    def check(self):
        """Check run statistics after test finished. To be overridden if needed."""
        pass

    def stop(self):
        """Stop testing when return True. To be overridden."""
        self.log.debug('Check for testing is over')
        return self.runs >= self.max_runs

    def sequencer(self, Trx: Transaction, stop: Callable = lambda: True, *args):
        """Generate randomized Trx while goal not achieved"""
        trx = Trx(*args)
        while True:
            if stop():
                self.log.info('Testing finished.')
                break
            self.log.info(f'Test case # {self.runs}')
            trx.randomize()
            yield trx
            self.runs += 1

    async def run_tb(self):
        """Run test cases."""
        await self.run()
        self.log.info(f'Finish tests. {self.runs} transactions were run.')
        self.coverage.final_report()
        raise self.scoreboard.result
