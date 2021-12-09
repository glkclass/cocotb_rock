# CocoTB. Base Monitor class

import logging as log
from typing import Iterable, Dict
from cocotb.handle import SimHandleBase
from cocotb_bus.monitors import BusMonitor as CocoTBBusMonitor


class BusMonitor(CocoTBBusMonitor):
    """"""

    _signals = None

    def __init__(
        self,
        entity: SimHandleBase,
        signals: [Iterable[str], Dict[str, str]] = None,
        name: str = None,
        clock: SimHandleBase = None,
        probes: Dict[str, SimHandleBase] = None,
        **kwargs
    ):
        self._signals = signals if signals is not None else self._signals
        super().__init__(entity, name, clock, **kwargs)
        self.probes = probes
        self.expected = []

    def add_expected(self, trx):
        """Store expected receive transactions to be checked in scoreboard"""
        self.expected.append(trx)

    async def receive(self):
        """Receive function. To be overridden."""
        raise NotImplementedError("Override ``receive`` method")

    async def _monitor_recv(self):
        while True:
            log.debug('_monitor_recv')
            self._recv(await self.receive())
