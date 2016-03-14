from __future__ import absolute_import

from decred.core.script import opcode
from decred.core import transaction

from hashmal_lib import plugins
from hashmal_lib.plugins import BasePluginUI, Plugin, augmenter
from hashmal_lib.core import chainparams
from hashmal_lib.core.serialize import Field
from hashmal_lib.core.transaction import TransactionSerializer, OutPoint, TxIn, TxOut

from .core.stack import DecredEngine

op_names = {}
ops_by_name = {}
disabled_ops = []
for op in opcode.opcodeArray:
    op_names[op.value] = op.name
    ops_by_name[op.name] = op.value
    if opcode.ParsedOpcode(op, b'').isDisabled():
        disabled_ops.append(op.value)

dcr_header_fields = [
    Field('nVersion', b'<i', 4, 1),
    Field('hashPrevBlock', 'hash', 32, b'\x00'*32),
    Field('hashMerkleRoot', 'hash', 32, b'\x00'*32),
    Field('hashStakeRoot', 'hash', 32, b'\x00'*32),
    Field('VoteBits', b'<H', 2, 0),
    Field('FinalState', 'bytes', 6, b'\x00'*6),
    Field('voters', b'<H', 2, 0),
    Field('FreshStake', b'<B', 1, 0),
    Field('revocations', b'<B', 1, 0),
    Field('PoolSize', b'<I', 4, 0),
    Field('nBits', b'<I', 4, 0),
    Field('nStakeBits', b'<q', 8, 0),
    Field('nHeight', b'<I', 4, 0),
    Field('size', b'<I', 4, 0),
    Field('nTime', b'<I', 4, 0),
    Field('nNonce', b'<I', 4, 0),
    Field('ExtraData', 'bytes', 36, b'\x00'*36)
]

dcr_tx_fields = [
    Field('nVersion', b'<i', 4, 1),
    Field('vin', 'inputs', None, None),
    Field('vout', 'outputs', None, None),
    Field('nLockTime', b'<I', 4, 0),
    Field('expiry', b'<I', 4, 0)
]

dcr_prevout_fields = [
    Field('hash', 'hash', 32, b'\x00'*32),
    Field('n', b'<I', 4, 0xffffffff),
    Field('tree', b'<b', 1, 0)
]

dcr_txin_fields = [
    # non witness
    Field('prevout', 'prevout', None, None),
    Field('nSequence', b'<I', 4, 0xffffffff),
    # witness
    Field('value', b'<q', 8, 0),
    Field('block_height', b'<I', 4, 0),
    Field('block_index', b'<I', 4, 0),
    Field('scriptSig', 'script', None, None),
]

dcr_txout_fields = [
    Field('nValue', b'<q', 8, -1),
    Field('version', b'<H', 2, 0),
    Field('scriptPubKey', 'script', None, None)
]

dcr_tx_help = dict(plugins.chainparams.btc_field_help)
dcr_tx_help[('expiry', b'<I', 4, 0)] = 'Transaction expiry height'
dcr_tx_help['prevout'][('tree', b'<b', 1, 0)] = 'Previous transaction tree'
#dcr_tx_help['input'][('prev_out', 'prevout', None, None)] = '
dcr_tx_help['input'][('value', b'<q', 8, 0)] = 'Unspent output value'
dcr_tx_help['input'][('block_height', b'<I', 4, 0)] = 'Unspent output block height'
dcr_tx_help['input'][('block_index', b'<I', 4, 0)] = 'Unspent output block transaction index'

dcr_builder_help = {
    'prevout': {
        ('tree', b'<b', 1, 0): ('Previous transaction tree', 'Use this to specify the tree that the output being spent is in.'),
    },
    'input': {
        ('value', b'<q', 8, 0): ('Unspent output value', 'Use this to specify the value of the output being spent.'),
        ('block_height', b'<I', 4, 0): ('Unspent output block height', 'Use this to specify the block that the output being spent is in.'),
        ('block_index', b'<I', 4, 0): ('Unspent output block transaction index', 'Use this to specify the index of the transaction containing the output being spent.')
    },
    'output': {
        ('version', b'<H', 2, 0): ('Output version', 'Use this to specify the version of the output.'),
    }
}

class DecredTxSerializer(TransactionSerializer):
    def stream_deserialize(self, tx, f):
        dtx = transaction.Transaction.stream_deserialize(f)
        vin = []
        for din in dtx.txins:
            pout_hash = din.prev_out.hash
            pout_n = din.prev_out.index
            pout_kwargs = {'tree': din.prev_out.tree}
            prevout = OutPoint(hash=pout_hash, n=pout_n, kwfields=pout_kwargs)

            txi_sequence = din.sequence
            txi_script = din.sig_script

            txi_value = din.value
            txi_height = din.block_height
            txi_index = din.block_index
            txi_kwargs = {'value': txi_value, 'block_height': txi_height, 'block_index': txi_index}
            txin = TxIn(prevout=prevout, scriptSig=txi_script, nSequence=txi_sequence, kwfields=txi_kwargs)
            vin.append(txin)

        vout = []
        for do in dtx.txouts:
            txo_val = do.value
            txo_version = do.version
            txo_script = do.pk_script
            txo_kwargs = {'version': txo_version}
            txout = TxOut(nValue=txo_val, scriptPubKey=txo_script, kwfields=txo_kwargs)
            vout.append(txout)

        kwargs = {
            'nVersion': dtx.version,
            'vin': vin,
            'vout': vout,
            'nLockTime': dtx.locktime,
            'expiry': dtx.expiry,
        }
        return kwargs

    def stream_serialize(self, tx, f):
        txins = []
        for i in tx.vin:
            po = transaction.OutPoint(i.prevout.hash, i.prevout.n, i.prevout.tree)
            txin = transaction.TxIn(prev_out=po, sequence=i.nSequence, value=i.value,
                        block_height=i.block_height, block_index=i.block_index,
                        sig_script=i.scriptSig)
            txins.append(txin)

        txouts = []
        for o in tx.vout:
            txout = transaction.TxOut(value=o.nValue, version=o.version, pk_script=o.scriptPubKey)
            txouts.append(txout)

        kwargs = {
            'version': tx.nVersion,
            'txins': txins,
            'txouts': txouts,
            'locktime': tx.nLockTime,
            'expiry': tx.expiry,
        }
        dtx = transaction.Transaction(**kwargs)
        return dtx.stream_serialize(f)

DecredPreset = chainparams.ParamsPreset(
        name='Decred',
        script_engine_cls = DecredEngine,
        opcode_names = op_names,
        opcodes_by_name = ops_by_name,
        disabled_opcodes = disabled_ops,
        prevout_fields = dcr_prevout_fields,
        txin_fields = dcr_txin_fields,
        txout_fields = dcr_txout_fields,
        tx_fields = dcr_tx_fields,
        tx_serializer = DecredTxSerializer,
        block_header_fields = dcr_header_fields
)


def make_plugin():
    p = Plugin(DecredTools)
    p.has_gui = False
    return p

class DecredTools(BasePluginUI):
    tool_name = 'Decred'
    description = 'Decred augments chainparams with a Decred preset.'

    @augmenter
    def chainparams_presets(self, *args):
        return DecredPreset

    @augmenter
    def transaction_field_help(self, *args):
        return {'Decred': dcr_tx_help}

    @augmenter
    def transaction_builder_field_help(self, *args):
        return {'Decred': dcr_builder_help}
