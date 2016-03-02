from collections import namedtuple

from hashmal_lib.core.utils import push_script
from hashmal_lib.core.stack import StackState

from decred.core.transaction import *
from decred.core import transaction
from decred.core.script.engine import *
from decred.core.script.scriptnum import *
from decred.core.script.opcode import OpcodeByName


Step = namedtuple('Step', ('stack', 'op'))

class DecredExecution(object):
    """Decred script execution."""
    def __init__(self):
        pass

    def evaluate(self, pk_script, tx=None, in_idx=0, flags=0):
        pass

class DecredEngine(object):
    """Decred script engine."""
    def __init__(self, pk_script, tx=None, in_idx=0, flags=None, execution_data=None):
        # Execution data is ignored as it is not needed.

        # Convert flags tuple to integer.
        intflags = 0
        if flags:
            for i in flags:
                intflags |= i
        flags = intflags

        self.verifying = True if tx else False
        if not tx:
            tx = transaction.Transaction(txins=(TxIn(),))
        else:
            tx = transaction.Transaction.deserialize(tx.serialize())
        self.engine = Engine(pk_script, tx, in_idx, flags, 0)
        self.error = None
        self.steps = []

        done = False
        while done != True:
            op = self.engine.disasm_pc(verbose=False)
            op = OpcodeByName.get(op)

            try:
                done = self.engine.step()
            except Exception as e:
                self.error = str(e)
                done = True

            stack_state = []
            for i in range(self.engine.dstack.depth()):
                s = self.engine.dstack.peek_bytearray(i)
                stack_state.append(s)
            stack_state.reverse()
            step = StackState(stack_state, op, '')
            self.steps.append(step)

        if not self.error:
            try:
                self.engine.check_error_condition(True)
            except Exception as e:
                self.error = e

    def __iter__(self):
        i = 0
        # Raise no error for "Script did not pass"
        if self.error and str(self.error) != 'execute fail, fail on stack':
            raise self.error
        while i < len(self.steps):
            yield self.steps[i]
            i += 1

