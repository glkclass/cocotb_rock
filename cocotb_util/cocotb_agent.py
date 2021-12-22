# CocoTB. Base Agent class

import logging
from typing import Optional, Any

from cocotb.handle import SimHandleBase
from cocotb.log import SimLog

from cocotb_util.cocotb_driver import BusDriver
from cocotb_util.cocotb_monitor import BusMonitor


class BusAgent(object):

    def __init__(
        self,
        driver: BusDriver = None,
        monitor: BusMonitor = None,
        **kwargs: Any
    ):
        self.log = SimLog("cocotb.agent")
        self.log.setLevel(logging.INFO)
        self.driver = driver
        self.monitor = monitor

if __name__ == "__main__":
    foo = BusAgent()

