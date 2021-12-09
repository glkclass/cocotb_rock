# Start point for tests. Do an init. No tests here.

import logging as log
# import os
# import time

from cocotb_util.cocotb_util import set_starttime


log.getLogger().setLevel(log.INFO)

# init test start time to handle test timeout scenario
set_starttime()
