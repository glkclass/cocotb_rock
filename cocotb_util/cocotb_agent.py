# CocoTB. Base Agent class

import logging as log
from typing import Optional, Any

from cocotb.handle import SimHandleBase
from cocotb_driver import BusDriver
from cocotb_monitor import BusMonitor


class BusAgent(object):

    def __init__(
        self,
        driver: BusDriver = None,
        monitor: BusMonitor = None,
        **kwargs: Any
    ):
        self.log = log.getLogger()
        self.log.setLevel(log.INFO)

        self.driver = driver
        self.monitor = monitor
