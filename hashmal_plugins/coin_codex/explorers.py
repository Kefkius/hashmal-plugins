

import bitcoin
from bitcoin.core import COutPoint, CTxIn, CTxOut, CTransaction, lx, x, b2x, b2lx

import hashmal_lib
from hashmal_lib.core import Script, Transaction
from hashmal_lib.plugins.blockchain import BlockExplorer, header_from_insight_block

def abe_parse_raw_tx(res):
    version = int(res.get('ver'))
    locktime = int(res.get('lock_time'))
    vin = []
    vout = []
    for i in res.get('in'):
        prev_txid = i['prev_out']['hash']
        prev_n = int(i['prev_out']['n'])
        tx_outpoint = COutPoint(lx(prev_txid), prev_n)

        scriptSig = Script(x( i['raw_scriptSig'] ))
        sequence = int(i['sequence'])
        
        tx_input = CTxIn(tx_outpoint, x(scriptSig.get_hex()), sequence)
        vin.append(tx_input)

    for o in res.get('out'):
        value = float(o['value'])
        value = int(value * pow(10, 8))

        script = Script(x( o['raw_scriptPubKey'] ))
        tx_output = CTxOut(value, x(script.get_hex()))
        vout.append(tx_output)

    tx = Transaction(vin, vout, locktime, version)
    return b2x(tx.serialize())

def insight_parse_raw_tx(res):
    version = int(res.get('version'))
    locktime = int(res.get('locktime'))
    vin = []
    vout = []
    for i in res.get('vin'):
        prev_txid = i['txid']
        prev_n = int(i['n'])

        seq = int(i['sequence'])
        script_asm = i['scriptSig']['asm']
        script = Script.from_human(script_asm)

        tx_outpoint = COutPoint(lx(prev_txid), prev_n)
        tx_input = CTxIn(tx_outpoint, x(script.get_hex()), seq)
        vin.append(tx_input)

    for o in res.get('vout'):
        value = float(o['value'])
        value = int(value * pow(10, 8))

        script_asm = o['scriptPubKey']['asm']
        script = Script.from_human(script_asm)

        tx_output = CTxOut(value, x(script.get_hex()))
        vout.append(tx_output)

    tx = Transaction(vin, vout, locktime, version)
    return b2x(tx.serialize())

LTC_Litecoinnet = type('LTC_Litecoinnet', (BlockExplorer,), {
            'name': 'Litecoin.net',
            'domain': 'http://explorer.litecoin.net',
            'routes': {'raw_tx': '/rawtx/'},
            'parsers': {'raw_tx': abe_parse_raw_tx}
})

MZC_Mazachain = type('MZC_Mazachain', (BlockExplorer,), {
            'name': 'Mazacha.in',
            'domain': 'https://mazacha.in',
            'routes': {'raw_tx': '/api/tx/', 'raw_header': '/api/block/'},
            'parsers': {'raw_tx': insight_parse_raw_tx, 'raw_header': header_from_insight_block}
})

my_explorers = {
    'Litecoin': [LTC_Litecoinnet()],
    'Mazacoin': [MZC_Mazachain()],
}
