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
        name: str = 'agent',
        **kwargs: Any
    ):
        self.name = name
        self.log = SimLog(f"cocotb.{name}")
        self.log.setLevel(logging.INFO)
        self.add_driver(driver)
        self.add_monitor(monitor)

    def add_driver(self, driver: BusDriver, name: str = 'driver'):
        self.driver = driver
        if self.driver is not None:
            self.driver.log = SimLog(f"cocotb.{self.name}.{name}")

    def add_monitor(self, monitor: BusMonitor, name: str = 'monitor'):
        self.monitor = monitor
        if self.monitor is not None:
            self.monitor.log = SimLog(f"cocotb.{self.name}.{name}")


if __name__ == "__main__":
    foo = BusAgent()
