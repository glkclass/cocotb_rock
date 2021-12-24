# CocoTB. Base Transaction class
from typing import Any

from cocotb.handle import SimHandleBase
from cocotb_bus.scoreboard import Scoreboard as CocoTBScoreboard
from cocotb.result import TestSuccess

from cocotb_util.cocotb_transaction import Transaction


class Scoreboard(CocoTBScoreboard):
    def __init__(self, dut: SimHandleBase, fail_immediately=True):
        super().__init__(dut, fail_immediately=fail_immediately)
        self.compare_fn = lambda a, b: a == b
        self.x_fn = None

    def add_interface(
            self,
            monitor,
            expected_output,
            compare_fn=None,  # custom compare func
            x_fn=None,  # transformation func
            reorder_depth=0,
            strict_type=True):

        super().add_interface(
            monitor=monitor,
            expected_output=expected_output,
            compare_fn=None,
            reorder_depth=reorder_depth,
            strict_type=strict_type)

        if compare_fn is not None:
            if callable(compare_fn):
                self.compare_fn = compare_fn
            else:
                raise TypeError(f"Expected a callable compare function but got {str(type(compare_fn))}")

        if x_fn is not None:
            if callable(x_fn):
                self.x_fn = x_fn
            else:
                raise TypeError(f"Expected a callable compare function but got {str(type(x_fn))}")

    def compare(self, got: Any, exp: Any, log, strict_type=True):
        """Compare func.
            1. Optional apply transformation func to expected trx.
            2. Call either base or custom 'compare func' impl.
            3. Store trx if don't match"""

        # Input transform
        expected_val = self.x_fn(exp) if self.x_fn is not None else exp
        log.debug(f"Compare {got} and {expected_val}")

        # Compare the types
        if strict_type and type(got) != type(exp):
            self.errors += 1
            log.error("Received transaction type is different than expected")
            log.info(f"Received: {str(type(got))} but expected {str(type(exp))}")
            exp.store_to_file()
            assert not self._imm, "Received transaction of wrong type. Set strict_type=False to avoid this."
            return

        # Compare trx content
        match = self.compare_fn(got, expected_val)

        if not match:
            self.errors += 1
            log.error(f"Received value: '{repr(got)}' doesn't match expected one: '{repr(expected_val)}")
            exp.store_to_file()
            assert not self._imm, "Received transaction don't match."

        # don't use base compare func due to 'deprecated' warnings
        # super().compare(got, expected_val, log, strict_type)

    @property
    def result(self):
        """Determine the test result, do we have any pending data remaining?

        Returns:
            :any:`TestFailure`: If not all expected output was received or
            error were recorded during the test.
        """
        fail = False
        for monitor, expected_output in self.expected.items():
            if callable(expected_output):
                self.log.debug("Can't check all data returned for %s since "
                               "expected output is callable function rather "
                               "than a list" % str(monitor))
                continue
            if len(expected_output):
                self.log.warning("Still expecting %d transactions on %s" %
                                 (len(expected_output), str(monitor)))
                for index, transaction in enumerate(expected_output):
                    self.log.info("Expecting %d:\n%s" %
                                  (index, repr(transaction)))
                    if index > 5:
                        self.log.info("... and %d more to come" %
                                      (len(expected_output) - index - 1))
                        break
                fail = True
        if fail:
            assert False, "Not all expected output was received"
        if self.errors:
            assert False, "Errors were recorded during the test"
        return TestSuccess()
