# Start point for tests. Do an init. No tests here.

import logging
# import os
# import time

from cocotb_util.cocotb_util import set_starttime


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


# init test start time to handle test timeout scenario
set_starttime()
