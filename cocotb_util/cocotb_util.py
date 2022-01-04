# CocoTB util
import os
import time

import logging

from cocotb.clock import Clock
from cocotb.triggers import Timer
from cocotb.handle import SimHandleBase
from cocotb.result import TestSuccess

# from cocotb_util.cocotb_testbench import TestBench

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


def set_starttime():
    """Store test start time (int number of seconds) to the env"""
    os.environ['COCOTB_START_TIME_SECONDS'] = str(int(time.time()))


def static_vars(**kwargs):
    """Static variable emulate"""
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


def timeout(func):
    """ Timeout decorator.
        Stop test when timeout achieved (appropriate env vars should be set up at the test start point)"""
    def inner(*args, **kwargs):
        duration_hours = os.environ.get('COCOTB_TIMEOUT_HOURS', None)
        start_time_sec = os.environ.get('COCOTB_START_TIME_SECONDS', None)

        if duration_hours is not None and start_time_sec is not None:
            run_time_sec = int(time.time()) - int(start_time_sec)

            if run_time_sec > int(duration_hours) * 3600:
                log.warning(f'Test timeout achieved. Run time: {run_time_sec}')
                # report final coverage after termination if use with TestBench() member
                if len(args) > 0 and getattr(args[0], 'report_coverage_final', None) is not None:
                    args[0].report_coverage_final()
                raise TestSuccess
        return func(*args, **kwargs)
    return inner


def clk_625MHz(clk_in):
    return Clock(clk_in, 1.6, units="ns").start()


def clk_1GHz(clk_in):
    return Clock(clk_in, 1, units="ns").start()


async def reset(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    reset_n.value = 1
    reset_n._log.debug("Reset complete")


def assign_probe_str(probe: SimHandleBase, msg: str):
    """Assign string msg to packed logic/bit vector. Use for debug to display python string msg in waveforms"""
    if not isinstance(probe, SimHandleBase):
        return
    msg = str.encode(msg)  # to byte arr
    n = min(len(msg), int(len(probe) / 8))  # min between msg length and buffer size
    probe.setimmediatevalue(0)  # cleanup
    for i in range(n):
        for j in range(8):
            probe[8 * (n - 1 - i) + j].value = (msg[i] >> j) & 1


def assign_probe_int(probe: SimHandleBase, val: int):
    """Assign int val to int var. Use for debug to display python int in waveforms"""
    if not isinstance(probe, SimHandleBase):
        return
    probe.value = val
