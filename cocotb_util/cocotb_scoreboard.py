# CocoTB. Base Transaction class

from typing import Iterable

from cocotb.handle import SimHandleBase

from cocotb_bus.scoreboard import Scoreboard as CocoTBScoreboard


class Scoreboard(CocoTBScoreboard):
    def __init__(self, dut: SimHandleBase):
        super().__init__(dut)
