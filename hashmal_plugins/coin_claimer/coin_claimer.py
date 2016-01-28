from bitcoin.core import x, lx, b2x, b2lx
from bitcoin.base58 import CBase58Data

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from hashmal_lib.core import Script
from hashmal_lib.core.transaction import Transaction, sighash_types, sighash_types_by_value
from hashmal_lib.core.utils import is_hex
from hashmal_lib.plugins.base import BaseDock, Plugin, Category
from hashmal_lib.gui_utils import monospace_font


def make_plugin():
    return Plugin(CoinClaimer)

def get_unsigned_outputs(tx):
    # sighash types for each input
    hash_types = []
    for i, txin in enumerate(tx.vin):
        sig = Script(txin.scriptSig).get_human().split()[-2]
        hash_type = int(sig[-2:], 16)
        hash_types.append(hash_type)

    # sighash type names
    hash_names = map(lambda i: sighash_types_by_value.get(i), hash_types)
    # No unsigned outputs if SIGHASH_ALL is used.
    if any('SIGHASH_ALL' in i for i in hash_names):
        return []

    unsigned_outputs = range(len(tx.vout))
    # Evaluate sighash types.
    for i, name in enumerate(hash_names):
        if 'SIGHASH_SINGLE' in name:
            unsigned_outputs.remove(i)
    return unsigned_outputs

def replace_outputs(tx, hash160):
    """Replace unsigned outputs in tx."""
    if not is_hex(hash160) and len(hash160.replace('0x', '')) == 40:
        raise ValueError('hash160 must be 40 hex digits.')
    out_script = Script.from_human('OP_DUP OP_HASH160 %s OP_EQUALVERIFY OP_CHECKSIG' % hash160)

    unsigned_outputs = get_unsigned_outputs(tx)
    if not unsigned_outputs:
        return tx
    new_tx = Transaction.from_tx(tx)
    for o in unsigned_outputs:
        new_tx.vout[o].scriptPubKey = out_script
    return new_tx


class ClaimableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(ClaimableModel, self).__init__()
        self.tx = None
        self.unsigned_outputs = []

    def set_tx(self, tx):
        self.beginResetModel()
        self.tx = tx
        self.unsigned_outputs = get_unsigned_outputs(self.tx)
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self.tx = None
        self.unsigned_outputs = []
        self.endResetModel()

    def columnCount(self, parent=QModelIndex()):
        return 2

    def rowCount(self, parent=QModelIndex()):
        if not self.tx:
            return 0
        return len(self.tx.vout)

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        data = None
        if section == 0:
            if role == Qt.DisplayRole:
                data = 'Output'
            elif role == Qt.ToolTipRole:
                data = 'Output Index'
        elif section == 1:
            if role == Qt.DisplayRole:
                data = 'Status'
            elif role == Qt.ToolTipRole:
                data = 'Output Status'

        return data

    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid() or not self.tx:
            return None

        data = None
        c = index.column()
        if c == 0:
            if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
                data = index.row()
        elif c == 1:
            is_unsigned = index.row() in self.unsigned_outputs
            if role in [Qt.DisplayRole, Qt.EditRole]:
                data = 'Unsigned' if is_unsigned else 'Signed'
            elif role == Qt.ToolTipRole:
                data = 'Unsigned output' if is_unsigned else 'Signed output'

        return data

class CoinClaimer(BaseDock):
    tool_name = 'Coin Claimer'
    description = 'Coin Claimer allows you to change unsigned outputs in transactions.'
    category = Category.Tx
    is_large = True

    def init_data(self):
        self.tx = None

    def create_layout(self):
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.raw_tx_edit = QPlainTextEdit()
        self.raw_tx_edit.textChanged.connect(self.check_raw_tx)
        self.raw_tx_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.raw_tx_edit.customContextMenuRequested.connect(self.raw_tx_context_menu)
        self.raw_tx_edit.setWhatsThis('Enter a raw transaction here to see if it has unspent outputs.')
        self.raw_tx_edit.setFixedHeight(80)
        rawtx_form = QFormLayout()
        rawtx_form.addRow('Raw tx:', self.raw_tx_edit)
        rawtx_form.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.destination_edit = QLineEdit()
        self.destination_edit.setPlaceholderText('Enter an address or hash160')
        self.destination_edit.textChanged.connect(self.check_destination)
        self.destination_edit.setWhatsThis('Enter the destination that unsigned coins will be sent to here.')
        self.claim_button = QPushButton('Replace Unsigned Outputs')
        self.claim_button.clicked.connect(self.do_claim)
        self.claim_button.setWhatsThis('Clicking this button will replace the destination in unsigned outputs with yours.')
        dest_hbox = QHBoxLayout()
        dest_hbox.addWidget(self.destination_edit, stretch=1)
        dest_hbox.addWidget(self.claim_button)
        form.addRow('Destination:', dest_hbox)

        self.result_edit = QPlainTextEdit()
        self.result_edit.setReadOnly(True)
        self.result_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.result_edit.customContextMenuRequested.connect(self.result_context_menu)
        self.result_edit.setWhatsThis('The resulting transaction with unsigned outputs changed is displayed here.')
        for i in [self.raw_tx_edit, self.result_edit]:
            i.setFont(monospace_font)
        form.addRow('Result tx:', self.result_edit)

        self.model = ClaimableModel()
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.view.verticalHeader().setVisible(False)
        self.view.setWhatsThis('The status of the transaction\'s outputs are displayed here.')

        vbox = QVBoxLayout()
        vbox.addLayout(rawtx_form)
        vbox.addWidget(self.view)
        vbox.addLayout(form)
        return vbox

    def raw_tx_context_menu(self, pos):
        menu = QMenu()
        self.handler.add_plugin_actions(self, menu, str(self.raw_tx_edit.toPlainText()))
        menu.exec_(self.raw_tx_edit.viewport().mapToGlobal(pos))

    def result_context_menu(self, pos):
        menu = QMenu()
        self.handler.add_plugin_actions(self, menu, str(self.result_edit.toPlainText()))
        menu.exec_(self.result_edit.viewport().mapToGlobal(pos))

    def check_destination(self):
        txt = str(self.destination_edit.text())
        # Variable substitution.
        if txt.startswith('$'):
            var_value = self.handler.get_plugin('Variables').ui.get_key(txt[1:])
            if var_value:
                return self.destination_edit.setText(var_value)

    def check_raw_tx(self):
        txt = str(self.raw_tx_edit.toPlainText())
        try:
            tx = Transaction.deserialize(x(txt))
        except Exception:
            tx = None
        self.tx = tx
        self.model.set_tx(tx)

    def do_claim(self):
        """Replace unsigned outputs."""
        if not self.tx:
            self.status_message('Invalid or nonexistent transaction.', True)
            return
        dest = str(self.destination_edit.text())
        hash160 = dest
        # Try to decode address
        try:
            raw = CBase58Data(dest).to_bytes()
            hash160 = '0x' + b2x(raw)
        except Exception:
            # Try to parse hash160
            if len(dest.replace('0x', '')) == 40:
                hash160 = dest

        if not is_hex(hash160) and len(hash160.replace('0x', '')) == 40:
            self.status_message('Could not parse destination: %s' % hash160, True)
            return

        if not get_unsigned_outputs(self.tx):
            self.status_message('There are no unsigned outputs.', True)
            return
        new_tx = replace_outputs(self.tx, hash160)

        self.result_edit.setPlainText(b2x(new_tx.serialize()))
        self.status_message('Successfully altered outputs: %s' % unsigned_outputs)
