# Test Rock SPI ports: write/read registers.
# Regs config is located in cfg/regs.json:reg addresses, bit_width, ...

import logging

import cocotb
from cocotb.triggers import Timer

from cocotb_util import cocotb_util
from rock_spi.rock_spi import RockTestBench


@cocotb.test()
async def test_spi_write(dut):

    dut.dtop_dut._log.setLevel(logging.INFO)

    # Create SPI agent for SPI #0
    spi_0_tb = RockTestBench(dut)

    # Init Rock
    dut.dtop_dut.I_SPI_SEL.value = 0
    dut.dtop_dut.I_TEST_EN.value = 0
    dut.dtop_dut.I_SCAN_EN.value = 0
    dut.dtop_dut.I_CHIP_ADDR.value = 0
    dut.dtop_dut.I_MCE.value = 0

    # Run MCE frame
    # cocotb.start_soon(emulate_mce_frame(dut))

    # Run Clocks
    cocotb.start_soon(cocotb_util.clk_1GHz(dut.dtop_dut.I_CLK_I))
    cocotb.start_soon(cocotb_util.clk_625MHz(dut.dtop_dut.I_CLK_M))

    # Reset Rock
    await cocotb_util.reset(dut.dtop_dut.I_RESET_N, 123.1)
    await Timer(20, units='ns')
    await spi_0_tb.run_tb()
