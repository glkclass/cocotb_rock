# CocoTB. Base Driver class

from typing import Any, Iterable, Dict

from cocotb.handle import SimHandleBase
from cocotb_bus.drivers import BusDriver as CocoTBBusDriver
from cocotb_util.cocotb_transaction import Transaction


class BusDriver(CocoTBBusDriver):
    # _signals = None

    def __init__(
        self,
        entity: SimHandleBase,
        signals: [Iterable[str], Dict[str, str]],
        name: str = None,
        clock: SimHandleBase = None,
        probes: Dict[str, SimHandleBase] = None,
        **kwargs: Any
    ):
        self._signals = signals if signals is not None else self._signals
        super().__init__(entity, name, clock, **kwargs)
        # probes
        self.probes = probes

    async def _driver_send(self, trx: Transaction, sync: bool = True):
        self.check_trx(trx)
        await self.driver_send(trx)

    async def driver_send(self, trx: Transaction):
        """Implementation for BusDriver. May consume time."""
        raise NotImplementedError("Override ``driver_send`` method")

    def check_trx(self, trx: Transaction):
        """Check applied trx consistency. To be overridden."""
        assert trx is not None
