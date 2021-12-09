# CocoTB. Base Driver class

from typing import Any, Iterable, Dict

from cocotb.handle import SimHandleBase
from cocotb_bus.drivers import BusDriver as CocoTBBusDriver


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

    async def _driver_send(self, trx, sync: bool = True):
        self.check_trx(trx)
        await self.driver_send(trx)

    async def driver_send(self, trx):
        """Implementation for BusDriver. May consume time."""
        pass

    def check_trx(self, trx):
        """Check applied trx consistency. To be overridden."""
        assert trx is not None
