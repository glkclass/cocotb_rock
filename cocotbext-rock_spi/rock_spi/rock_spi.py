from typing import Iterable, Mapping, Any
import numpy as np
import logging
import importlib

import cocotb
from cocotb.triggers import RisingEdge as RE, FallingEdge as FE, Timer
from cocotb.handle import SimHandleBase
# from cocotb_coverage.coverage import *
cocotb_coverage = importlib.import_module('cocotb-coverage.cocotb_coverage.coverage')
coverage_db = cocotb_coverage.coverage_db

from scrpt.file import load
from cocotb_util.cocotb_util import assign_probe_str, assign_probe_int
from cocotb_util.cocotb_driver import BusDriver
from cocotb_util.cocotb_monitor import BusMonitor
from cocotb_util.cocotb_agent import BusAgent
from cocotb_util.cocotb_scoreboard import Scoreboard
from cocotb_util.cocotb_transaction import Transaction

from cocotb_util.cocotb_coverage import CoverPoint, CoverCross
from cocotb_util.cocotb_coverage_processor import CoverProcessor
from cocotb_util.cocotb_testbench import TestBench
from cocotb_util import cocotb_util

CHIP_ID = 3  # Hardcoded in RTL
CHIP_ADDR = 0  # 3-bit chip addr, defined by ROCK external inputs


class RockSpiDriver(BusDriver):
    def __init__(
        self,
        # hard config
        entity: SimHandleBase,
        spi_signals: Iterable[str] = ["i_sclk", "i_cs_n", "i_mosi", "o_miso"],
        spi_idx: int = 0,
        freq_mhz: float = 12.5,
        probes: Mapping[str, SimHandleBase] = None,
        # soft config
        chip_addr: int = 0
    ):

        signals = {sig: f'{sig.upper()}_{spi_idx}' for sig in spi_signals}
        super().__init__(
            entity,
            signals=signals,
            probes=probes)

        # SPI bus config
        self.sclk_half_period_us = 1 / (2 * freq_mhz)
        self.chip_addr = chip_addr
        self.n_sclk = 32
        self.brd = 0  # no broadcast
        self.rsv = 0  # reserved bit
        self.stop_bit = 1  # stop bit

        # init SPI bus
        self.bus.i_sclk.value = 0
        self.bus.i_cs_n.value = 1
        self.bus.i_mosi.value = cocotb.handle.BinaryValue('x')

    async def gen_cs_sclk(self, n_sclk=None):
        """Generate 'cs' and 'clk'"""
        self.log.debug(f"Generating cs and sclk")
        n_sclk = n_sclk if n_sclk is not None else self.n_sclk
        self.bus.i_cs_n.value = 0
        for i in range(n_sclk):
            self.bus.i_sclk.value = 0
            await Timer(self.sclk_half_period_us, units="us")
            self.bus.i_sclk.value = 1
            await Timer(self.sclk_half_period_us, units="us")
        self.bus.i_sclk.value = 0
        await Timer(20, units='ns')
        self.bus.i_cs_n.value = 1

    def check_trx(self, trx):
        """Check applied trx consistency"""
        error_msg = f'Wrong trx: {trx}!!!'
        assert isinstance(trx, Transaction), error_msg
        assert hasattr(trx, 'reg_addr'), error_msg
        assert hasattr(trx, 'reg_data'), error_msg
        assert hasattr(trx, 'wrn'), error_msg
        assert isinstance(trx.wrn, int), error_msg
        assert isinstance(trx.reg_addr, int), error_msg
        assert isinstance(trx.reg_data, int), error_msg

        assert trx.wrn in [0, 1], error_msg
        assert trx.reg_addr >= 0 and trx.reg_addr < 2**8, error_msg
        assert trx.reg_data >= 0 and trx.reg_data < 2**16, error_msg

    async def driver_send(self, trx: Transaction):
        """Write/Read trx.
            Wr mode: Send one trx
            Rd mode: Send first trx. Then send second trx wo input data to provide 'cs' and 'clk'
            for reading response on output"""

        self.log.info(f"Sending {repr(trx)}")

        cocotb.start_soon(self.gen_cs_sclk())
        for i in reversed(range(self.n_sclk)):
            await RE(self.bus.i_sclk)
            if i in [31, 30, 29]:
                wr_info = 'Chip addr'
                self.bus.i_mosi.value = (self.chip_addr >> (i - 29)) & 1
            elif i == 28:
                wr_info = 'WRn'
                self.bus.i_mosi.value = trx.wrn
            elif i == 27:
                wr_info = 'Br'
                self.bus.i_mosi.value = self.brd
            elif i in range(19, 27):
                wr_info = 'Reg addr'
                self.bus.i_mosi.value = (trx.reg_addr >> (i - 19)) & 1
            elif i in range(3, 19):
                wr_info = 'Reg data'
                self.bus.i_mosi.value = (trx.reg_data >> (i - 3)) & 1
            elif i in [1, 2]:
                wr_info = 'Rsv'
                self.bus.i_mosi.value = self.rsv
            elif i == 0:
                wr_info = 'Stp'
                self.bus.i_mosi.value = self.stop_bit
            else:
                wr_info = 'X'
            assign_probe_str(self.probes.get('wr_info', None), wr_info)
            assign_probe_int(self.probes.get('i', None), i)
            await Timer(1, units='ns')
            self.log.debug(f'{wr_info} : {i} : {self.bus.i_mosi.value}')

        await RE(self.bus.i_cs_n)
        self.bus.i_mosi.value = cocotb.handle.BinaryValue('x')
        assign_probe_str(self.probes.get('wr_info', None), '')
        self.log.debug(f"Finish sending trx: {trx}")
        await Timer(200, units='ns')  # pause between trx
        self.log.debug(f"Finish pause after trx")

        # Second trx when reading
        if trx.wrn == 0:
            self.log.debug(f"Starting read response trx")
            assign_probe_str(self.probes.get('wr_info', None), 'Read response trx')
            await self.gen_cs_sclk()
            assign_probe_str(self.probes.get('wr_info', None), '')
            self.log.debug(f"Finish read response trx")
            await Timer(np.random.randint(10, 200), units='ns')  # random pause between trx
            self.log.debug(f"Finish pause after trx")


class RockSpiMonitor(BusMonitor):
    """"""

    def __init__(
        self,
        # hard config
        entity: SimHandleBase,
        spi_signals: Iterable[str],
        spi_idx: int = 0,
        freq_mhz: float = 12.5,
        probes: Mapping[str, SimHandleBase] = None,
        # soft config
        chip_addr: int = 0
    ):
        signals = {sig: f'{sig.upper()}_{spi_idx}' for sig in spi_signals}
        super().__init__(
            entity,
            signals=signals,
            probes=probes)

        # SPI bus hard config
        self.sclk_half_period_us = 1 / (2 * freq_mhz)
        self.n_sclk = 32
        self.brd = 0  # no broadcast
        self.rsv = 0  # reserved bit
        self.stop_bit = 1  # stop bit
        # soft config
        self.chip_addr = chip_addr  # we should listen only given chip_addr

    async def receive(self):
        while True:
            # wait for read request
            await FE(self.bus.i_cs_n)
            chip_addr_wr = 0
            reg_addr = 0
            reg_data_wr = 0
            reg_data_rd = 0
            for i in reversed(range(self.n_sclk)):
                await FE(self.bus.i_sclk)
                assert self.bus.i_mosi.value.binstr in ['0', '1']
                if i in [31, 30, 29]:
                    rd_info = 'Chip addr wr'
                    chip_addr_wr = (chip_addr_wr << 1) | self.bus.i_mosi.value
                elif i == 28:
                    if (self.bus.i_mosi.value == 0):
                        wrn = 0
                        rd_info = 'Rd op'
                        self.log.debug('Read request detected')
                    else:
                        wrn = 1
                        rd_info = 'Wr op'
                elif i in range(19, 27):
                    rd_info = 'Reg addr'
                    reg_addr = (reg_addr << 1) | self.bus.i_mosi.value
                elif i in range(3, 19):
                    rd_info = 'Reg data written'
                    reg_data_wr = (reg_data_wr << 1) | self.bus.i_mosi.value
                elif i == 0:
                    rd_info = 'Stp'
                    assert self.bus.i_mosi.value == self.stop_bit
                else:
                    rd_info = 'X'
                self.log.debug(f'{rd_info} : {i} : {self.bus.i_mosi.value}')
                assign_probe_str(self.probes.get('rd_info', None), rd_info)
                assign_probe_int(self.probes.get('i', None), i)

            # handle read response
            if wrn == 0:
                chip_addr_rd = 0
                status = ''
                await FE(self.bus.i_cs_n)
                self.log.debug(f"Starting reading response")
                for i in reversed(range(self.n_sclk)):
                    await FE(self.bus.i_sclk)
                    assert self.bus.o_miso.value.binstr in ['0', '1']
                    if i in [31, 30, 29, 28, 27, 26]:
                        rd_info = 'Zero bits'
                        # assert self.bus.o_miso.value == 0
                    elif i == 25:
                        rd_info = 'One bit'
                    elif i in [24, 23, 22]:
                        rd_info = 'Chip addr rd'
                        chip_addr_rd = (chip_addr_rd << 1) | self.bus.o_miso.value
                    elif i == 21:
                        rd_info = 'WRn'
                        assert chip_addr_wr == chip_addr_rd, "Chip addr mismatch"
                    elif i == 20:
                        rd_info = 'Br'
                    elif i in range(4, 20):
                        rd_info = 'Reg data'
                        reg_data_rd = (reg_data_rd << 1) | self.bus.o_miso.value
                    elif i == 3:
                        rd_info = 'Status'
                        status = "Ok" if self.bus.o_miso.value.binstr == '0' else 'Error'
                        assert status == 'Ok', "Error read status detected!"
                    elif i in [2, 1, 0]:
                        rd_info = 'Zero bits'
                        # assert self.bus.o_miso.value.binstr == '0'
                    else:
                        rd_info = 'X'
                    assign_probe_str(self.probes.get('rd_info', None), rd_info)
                    assign_probe_int(self.probes.get('i', None), i)
                    await Timer(1, units='ns')
                    self.log.debug(f'{rd_info} : {i} : {self.bus.o_miso.value}')

                await RE(self.bus.i_cs_n)
                self.log.debug(f"Finish reading response")
                self.log.info(f'Read trx: Chip addr={chip_addr_rd} : Data={reg_data_rd} : Status={status}')

            reg_data = reg_data_rd if wrn == 0 else reg_data_wr
            self.log.debug(f"Monitor recieved: {wrn}, {reg_addr}, {reg_data}")
            return wrn, reg_addr, reg_data


class RockSpiAgent(BusAgent):

    def __init__(
        self,
        # hard config
        entity: SimHandleBase = None,
        name: str = None,
        spi_idx: int = 0,
        freq_mhz: float = 12.5,
        driver: str = 'on',
        monitor: str = 'on',
        # soft config
        chip_addr: int = 0,
    ):
        super().__init__()

        self.rock_spi_signals = ["i_sclk", "i_cs_n", "i_mosi", "o_miso"]

        self.add_driver(
            RockSpiDriver(
                entity,
                spi_signals=self.rock_spi_signals,
                spi_idx=spi_idx,
                freq_mhz=freq_mhz,
                chip_addr=chip_addr) if driver.lower() == 'on' else None
        )

        self.add_monitor(
            RockSpiMonitor(
                entity,
                spi_signals=self.rock_spi_signals,
                spi_idx=spi_idx,
                freq_mhz=freq_mhz,
                chip_addr=chip_addr) if monitor.lower() == 'on' else None
        )

class RockSpiTrx(Transaction):

    def __init__(self, *args):
        super().__init__(['reg_name', 'reg_addr', 'reg_data', 'wrn', 'reg_data_range', 'read_reg_data_expected'])

        # get regs external config
        assert len(args) == 1
        assert isinstance(args[0], dict)

        self.cfg = args[0]
        self.regs = self.cfg['regs']

        self.covered_regs = self.cfg.get('covered_regs', None)
        assert self.covered_regs is not None

        self.read_reg_data_expected = None  # will be used to store expected read value for coverage collect
        self.reg_data_range = None  # we randomize 5 diff data values/ranges

        self.add_rand('wrn', [0, 1])
        self.add_rand('reg_name', self.cfg['reg_names'])

        self.reg_data_range_weights = {'min0': 1, 'min1': 1, 'mid': 1, 'max0': 1, 'max1': 1}
        self.add_rand('reg_data_range', list(self.reg_data_range_weights.keys()))

        def reg_name_cstr(reg_name):
            """Soft constraint not to except when all regs will be covered"""
            return int(reg_name not in self.covered_regs)  # read-only regs

        def wrn_cstr(reg_name, wrn):
            # return wrn in list(range(self.regs[reg_name]['r_w'] + 1))
            if self.regs[reg_name]['r_w'] == 0:
                return wrn == 0  # read-only regs
            else:
                return wrn in [0, 1]

        def reg_data_cstr(reg_data_range, wrn):
            if wrn == 1:
                return self.reg_data_range_weights[reg_data_range]
            else:
                return True   # doesn't matter

        self.add_constraint(wrn_cstr)
        self.add_constraint(reg_data_cstr)
        self.solve_order('reg_name', 'wrn', 'reg_data_range')

    def post_randomize(self):
        self.reg_addr = self.regs[self.reg_name]['addr']

        max_val = self.regs[self.reg_name]['max_val']
        self.reg_data = {
            'min0': 0,
            'min1': 1,
            'mid': np.random.randint(0, max_val + 1),
            'max0': max_val - 1,
            'max1': max_val
        }[self.reg_data_range]

        self.read_reg_data_expected = None
        self.log.debug(repr(self))


class RockSpiCoverProcessor(CoverProcessor):
    def __init__(self, **kwargs):

        coverage_report_cfg = {
            'status': {
                'top.reg_data': ['new_hits', 'covered_bins'],
                'top.reg_name_rw_data_cross': ['cover_percentage', 'new_hits', 'covered_bins', 'bin_cnt']
            },
            'final': {'bins': True}
        }

        # get regs config
        assert 'reg_cfg' in kwargs
        self.reg_cfg = kwargs['reg_cfg']
        self.regs = self.reg_cfg['regs']
        super().__init__(report_cfg=coverage_report_cfg)

    def define(self):
        self.log.info('Define coverage')

        def rel_reg_data(trx, bin):
            max_val = self.regs[trx.reg_name]['max_val']
            check_value = trx.reg_data if trx.wrn == 1 else trx.read_reg_data_expected

            if bin == 'min0':
                return check_value == 0
            elif bin == 'min1':
                return check_value == 1
            elif bin == 'max0':
                return check_value == max_val
            elif bin == 'max1':
                return check_value == (max_val - 1)
            elif bin == 'mid':
                return 0 <= check_value <= max_val if max_val < 4 else 2 <= check_value <= (max_val - 2)
            else:
                return False

        self.add_cover_items(
            CoverPoint(
                "top.reg_name",
                xf=lambda trx: trx.reg_name,
                bins=self.reg_cfg['reg_names']
            ),

            CoverPoint(
                "top.rw",
                xf=lambda trx: trx.wrn,
                bins=[0, 1]
            ),

            CoverPoint(
                "top.reg_data",
                xf=lambda trx: trx,
                bins=['min0', 'min1', 'max0', 'max1', 'mid'],
                rel=rel_reg_data,
                inj=False
            ),

            CoverCross(
                name="top.reg_name_rw_data_cross",
                items=["top.reg_name", "top.rw", "top.reg_data"],
                ign_bins=[("CHIP_ID_ADDR", 1, None), ("CHIP_VERSION_ADDR", 1, None), ("SPI_STATUS_ADDR", 1, None)],
            )
        )

class RockTestBench(TestBench):

    def __init__(
        self,
        dut: SimHandleBase
    ):

        super().__init__()
        self.dut = dut

        self.agent = RockSpiAgent(
            dut.dtop_dut,
            spi_idx=0,
            driver='on',
            monitor='on',
            chip_addr=0
        )
        self.agent.driver.probes = {'wr_info': dut.probes.wr_info, 'i': dut.probes.i}
        self.agent.monitor.probes = {'rd_info': dut.probes.rd_info, 'i': dut.probes.i}
        self.agent.monitor.add_callback(self.catch_reset)

        self.scoreboard = Scoreboard(dut.dtop_dut, fail_immediately=True)
        self.scoreboard.add_interface(
            self.agent.monitor,
            self.agent.monitor.expected,
            compare_fn=None,
            x_fn=lambda trx: (trx.wrn, trx.reg_addr, trx.read_reg_data_expected if trx.wrn == 0 else trx.reg_data),
            strict_type=True)

        self.coverage = RockSpiCoverProcessor(reg_cfg=self.cfg)

        # self.agent.monitor.log.setLevel(logging.DEBUG)
        # self.agent.driver.log.setLevel(logging.DEBUG)
        # self.scoreboard.log.setLevel(logging.DEBUG)
        # self.coverage.log.setLevel(logging.DEBUG)

        self.max_runs = 2

    def catch_reset(self, got):
        """Catch reset trx and reset written reg content"""
        assert isinstance(got, (tuple, list)) and len(got) == 3
        WRN = 1
        RESET_REG_ADDR = 2
        RESET_REG_CODE = 9
        if got[0] == WRN and got[1] == RESET_REG_ADDR and got[2] == RESET_REG_CODE:
            self.warning('Reset Regs')
            for reg in self.regs:
                del self.regs[reg]['reg_value']

    def init(self):
        """ 1. Load Reg config.
            2. Extend regs config with 'array of regs'.
            3. Prepare weights for random test generation"""

        # Load Reg config
        # self.cfg = load('cfg/regs.json', 'json')
        self.cfg = cfg
        self.regs = self.cfg['regs']
        self.cfg['covered_regs'] = []

        # Init Rd only default values
        self.regs['CHIP_ID_ADDR']['reset_reg_value'] = (CHIP_ID << 4) | CHIP_ADDR

        # Remove 'unsupported Regs'
        unsupported_regs = []
        for reg_name in self.regs:
            if self.regs[reg_name].get('unsupported', None) is not None:
                unsupported_regs.append(reg_name)
        for reg_name in unsupported_regs:
            del self.regs[reg_name]

        # Handle array regs. There two 'array reg' pseudo-records which need to be replaced with array of regs
        array_reg_names = [reg_name for reg_name in list(self.regs.keys()) if self.regs[reg_name].get('n_regs', 1) > 1]

        for array_reg_name in array_reg_names:
            if array_reg_name == 'ANODE_BIAS_ADDR':
                start_addr = self.regs[array_reg_name]['addr']
                for reg_i in range(self.regs[array_reg_name]['n_regs']):
                    reg_i_name = f'ANODE_BIAS_{reg_i}_ADDR'
                    self.regs[reg_i_name] = {
                                            'addr':         start_addr + reg_i,
                                            'bit_width':    self.regs[array_reg_name]['bit_width'],
                                            'r_w':          self.regs[array_reg_name]['r_w'],
                                            'reset_reg_value':    self.regs[array_reg_name]['reset_reg_value']

                                        }
                del self.regs[array_reg_name]  # remove array reg pseudo-record

            elif array_reg_name == 'MBIST_RES_ADDR':
                start_addr = self.regs[array_reg_name]['addr']
                for reg_i in range(int(self.regs[array_reg_name]['n_regs'] / 3)):
                    for j in range(3):
                        reg_i_name = f'MBIST_RES{reg_i}_{j}_ADDR'
                        self.regs[reg_i_name] = {
                                                'addr':         start_addr + reg_i * 3 + j,
                                                'bit_width':    12 if j == 0 else 9,
                                                'r_w':          self.regs[array_reg_name]['r_w']
                                            }
                del self.regs[array_reg_name]  # remove array reg pseudo-record

            else:
                assert False, "Missed array Reg"

        self.cfg['reg_names'] = list(self.regs.keys())
        # for key in cfg['reg_names']:
        #     print(f'{key:24}:{self.regs[key]}')

        # Calc max reg values
        for reg_name in self.cfg['reg_names']:
            self.regs[reg_name]['max_val'] = (1 << self.regs[reg_name]['bit_width']) - 1

    async def emulate_mce_frame(self, dut):
        """"Emulate MCE frame with random timing in parallel to SPI access to provocate 'postponed SPI regs write' mechanism usage"""
        await Timer(20, units='ns')
        while 1:
            mce_high_length = np.random.randint(1900, 2100)
            mce_low_length = np.random.randint(50, 250)
            dut.dtop_dut.I_MCE.value = 1
            await Timer(mce_high_length, units='ns')
            dut.dtop_dut.I_MCE.value = 0
            await Timer(mce_low_length, units='ns')

    def stop(self):
        """Stop testing when test goal achieved."""
        return (self.runs >= self.max_runs
            or coverage_db['top.reg_name_rw_data_cross'].cover_percentage == 100)

    async def run(self):
        """Send transactions. Store expected responces."""
        cocotb.start_soon(self.emulate_mce_frame(self.dut))

        for trx in self.sequencer(RockSpiTrx, self.stop, self.cfg):
            # store info about runs: list of wr(1) or rd(0) runs
            run_trx = self.regs[trx.reg_name].get('run_trx', None)
            if run_trx is None:
                self.regs[trx.reg_name]['run_trx'] = []
            self.regs[trx.reg_name]['run_trx'].append(trx.wrn)

            if trx.wrn == 0:  # read op
                # extract last written data if exists and add to list of golds
                read_reg_value_expected = self.regs[trx.reg_name].get('reg_value', None)
                if read_reg_value_expected is None:
                    read_reg_value_expected = self.regs[trx.reg_name].get('reset_reg_value', 0)
                trx.read_reg_data_expected = read_reg_value_expected
            else:  # write op
                # store written reg data
                self.regs[trx.reg_name]['reg_value'] = trx.reg_data

            self.log.info(trx)
            self.agent.monitor.add_expected(trx)

            await self.agent.driver.send(trx)
            self.coverage.collect(trx)




cfg = {
    "n_regs": 77,

    "regs":
    {
        "CHIP_ID_ADDR":
        {
            "addr":         0,
            "bit_width":    16,
            "r_w":          0,
            'max_val':      16383
        },

        "res":
        {
            "addr":         2,
            "bit_width":    4,
            "r_w":          1,
            'max_val':      15
        },


        "gamma":
        {
            "addr":         4,
            "bit_width":    1,
            "r_w":          1,
            'max_val':      1
        },

        "psi":
        {
            "addr":         147,
            "bit_width":    9,
            "n_regs":       1,
            "r_w":          1,
            'max_val':      511

        }
    }
}


if __name__ == "__main__":
    cfg['reg_names'] = list(cfg['regs'].keys())

    foo = RockSpiTrx(cfg)

    for _ in range(100):
        foo.randomize()
