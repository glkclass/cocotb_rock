# CocoTB. Base TestBench class

import logging as log
from typing import Any

from cocotb_util import cocotb_util
from cocotb_agent import BusAgent
from cocotb_scoreboard import Scoreboard
from cocotb_util.cocotb_transaction import Transaction


class TestBench(object):

    def __init__(
        self,
        agent: BusAgent = None,
        scoreboard: Scoreboard = None,
        **kwargs: Any
    ):
        self.log = log.getLogger()
        self.log.setLevel(log.INFO)

        self.agent = agent
        self.scoreboard = scoreboard
        self.runs = 0
        self.max_runs = 1

    def init(self):
        """Init TestBench before test started. To be overridden."""
        pass

    async def run(self):
        """ Run tests cases. To be overridden."""
        for trx in self.sequencer(Transaction):
            if self.agent.monitor is not None:
                self.agent.monitor.add_expected(trx)
            if self.agent.driver is not None:
                await self.agent.driver.send(trx)

    def check(self):
        """Check run statistics after test finished. To be overridden."""
        pass

    @cocotb_util.timeout
    def goal_achieved(self):
        """Stop testing when test goal achieved. To be overridden."""
        return self.runs >= self.max_runs

    def sequencer(self, Trx: Transaction, *args):
        """Generate Trx while goal not achieved"""
        while not self.goal_achieved():
            # choose register randomly
            self.log.info(f'Test case # {self.runs}')
            yield Trx(*args).randomize()
            self.runs += 1

    async def run_tb(self):
        """Run test cases."""
        self.init()
        await self.run()
        raise self.scoreboard.result
        self.log.info(f'Finish tests. {self.runs} transactions were run.')
        self.check()
