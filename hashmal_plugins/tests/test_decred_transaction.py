import unittest
from collections import namedtuple

from bitcoin.core import x, b2x

from hashmal_lib.core import chainparams
from hashmal_lib.core.transaction import Transaction
from hashmal_lib import gui_utils

from hashmal_plugins.decred_tools.hashmal_decred import (DecredPreset, dcr_header_fields, dcr_tx_fields,
            dcr_prevout_fields, dcr_txin_fields, dcr_txout_fields)

chainparams.add_preset(DecredPreset)

class TransactionTest(unittest.TestCase):
    def setUp(self):
        super(TransactionTest, self).setUp()
        chainparams.set_to_preset('Decred')
    
    def test_transaction_deserialization_and_serialization(self):
        # Transaction from Decred unit test.
        raw_tx = x('01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff00ffffffff0200f2052a01000000abab434104d64bdfd09eb1c5fe295abdeb1dca4281be988e2da0b6c1c6a59dc226c28624e18175e851c96b973d81b01cc31f047834bc06d6d6edf620d184241a6aed8b63a6ac00e1f50500000000bcbc434104d64bdfd09eb1c5fe295abdeb1dca4281be988e2da0b6c1c6a59dc226c28624e18175e851c96b973d81b01cc31f047834bc06d6d6edf620d184241a6aed8b63a6ac00000000000000000112121212121212121515151534343434070431dc001b0162')
        tx = Transaction.deserialize(raw_tx)

        self.assertEqual(1, tx.nVersion)
        self.assertEqual(0, tx.nLockTime)
        self.assertEqual(0, tx.expiry)

        # Test input.
        self.assertEqual(1, len(tx.vin))
        txin = tx.vin[0]
        self.assertEqual(1302123111085380114, txin.value)
        self.assertEqual(353703189, txin.block_height)
        self.assertEqual(875836468, txin.block_index)
        self.assertEqual(x('0431dc001b0162'), txin.scriptSig)
        self.assertEqual(4294967295, txin.nSequence)

        self.assertEqual(2, len(tx.vout))
        # Test output 0.
        txout = tx.vout[0]
        self.assertEqual(5000000000, txout.nValue)
        self.assertEqual(43947, txout.version)
        self.assertEqual(x('4104d64bdfd09eb1c5fe295abdeb1dca4281be988e2da0b6c1c6a59dc226c28624e18175e851c96b973d81b01cc31f047834bc06d6d6edf620d184241a6aed8b63a6ac'), txout.scriptPubKey)
        # Test output 1.
        txout = tx.vout[1]
        self.assertEqual(100000000, txout.nValue)
        self.assertEqual(48316, txout.version)
        self.assertEqual(x('4104d64bdfd09eb1c5fe295abdeb1dca4281be988e2da0b6c1c6a59dc226c28624e18175e851c96b973d81b01cc31f047834bc06d6d6edf620d184241a6aed8b63a6ac'), txout.scriptPubKey)

        self.assertEqual(b2x(raw_tx), b2x(tx.serialize()))

LabelTest = namedtuple('LabelTest', ('attr', 'label'))

class ViewLabelTest(unittest.TestCase):
    def test_view_label_for_decred_block_headers(self):
        labels = [
            'Version',
            'Prev Block Hash',
            'Merkle Root Hash',
            'Stake Root Hash',
            'Vote Bits',
            'Final State',
            'Voters',
            'Fresh Stake',
            'Revocations',
            'Pool Size',
            'Bits',
            'Stake Bits',
            'Height',
            'Size',
            'Time',
            'Nonce',
            'Extra Data'
        ]
        test_items = [LabelTest(*i) for i in zip([field[0] for field in dcr_header_fields], labels)]
        for test in test_items:
            self.assertEqual(test.label, gui_utils.get_label_for_attr(test.attr))

    def test_view_label_for_decred_txin_fields(self):
        labels = [
            'Prevout',
            'Sequence',
            'Value',
            'Block Height',
            'Block Index',
            'Sig Script'
        ]
        test_items = [LabelTest(*i) for i in zip([field[0] for field in dcr_txin_fields], labels)]
        for test in test_items:
            self.assertEqual(test.label, gui_utils.get_label_for_attr(test.attr))

    def test_view_label_for_decred_txout_fields(self):
        labels = [
            'Value',
            'Version',
            'Pub Key Script'
        ]
        test_items = [LabelTest(*i) for i in zip([field[0] for field in dcr_txout_fields], labels)]
        for test in test_items:
            self.assertEqual(test.label, gui_utils.get_label_for_attr(test.attr))
