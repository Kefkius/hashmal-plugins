from bitcoin.core import x, lx, b2x, b2lx
import pycoin
from pycoin.key.BIP32Node import BIP32Node

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import hashmal_lib
from hashmal_lib.plugins.base import BaseDock, Plugin, Category, augmenter
from hashmal_lib.plugins.item_types import Item, ItemAction
from hashmal_lib.gui_utils import AmountEdit, floated_buttons, Separator, monospace_font


def make_plugin():
    return Plugin(Pycoin)

class ExtKeyItem(Item):
    name = 'Extended Key'
    @classmethod
    def coerce_item(cls, data):
        def coerce_base58(v):
            key = BIP32Node.from_hwif(v)
            return key

        for i in [coerce_base58]:
            try:
                value = i(data)
                if value:
                    return cls(value)
            except Exception:
                continue

    def __str__(self):
        return self.value.as_text()

    def raw(self):
        return b2x(self.value.serialize())

class ExtKeyModel(QAbstractTableModel):
    """Model of an extended key."""
    DEPTH = 0
    FPRINT = 1
    CHILD_NUM = 2
    CHAINCODE = 3
    PUBKEY = 4
    PARENT_FPRINT = 5
    IS_PRIVATE = 6
    PRIVKEY = 7
    BASE58 = 8
    def __init__(self, parent=None):
        super(ExtKeyModel, self).__init__(parent)
        self.extkey = None

    def set_key(self, key):
        self.beginResetModel()
        self.extkey = key
        self.endResetModel()

    def clear(self):
        self.set_key(None)

    def rowCount(self, parent = QModelIndex()):
        return 1

    def columnCount(self, parent = QModelIndex()):
        return 9

    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid() or self.extkey is None:
            return None

        data = None
        col = index.column()
        key = self.extkey

        if role in [Qt.DisplayRole, Qt.EditRole]:
            if col == self.DEPTH:
                data = key.tree_depth()
            elif col == self.FPRINT:
                data = b2x(key.fingerprint())
            elif col == self.CHILD_NUM:
                data = key.child_index()
            elif col == self.CHAINCODE:
                data = b2x(key.chain_code())
            elif col == self.PUBKEY:
                data = key.sec_as_hex()
            elif col == self.PARENT_FPRINT:
                data = b2x(key.parent_fingerprint())
            elif col == self.IS_PRIVATE:
                data = key.is_private()
            elif col == self.PRIVKEY:
                data = '%x' % key.secret_exponent() if key.is_private() else ''
            elif col == self.BASE58:
                data = key.as_text()

        return QVariant(data)

class ExtKeyWidget(QWidget):
    def __init__(self, parent=None):
        super(ExtKeyWidget, self).__init__(parent)

        self.depth = QLineEdit()
        self.fingerprint = QLineEdit()
        self.child_index = QLineEdit()
        self.chain_code = QLineEdit()
        self.public_key = QLineEdit()
        self.parent_fingerprint = QLineEdit()

        self.private_key_hex = QLineEdit()
        for i in [self.fingerprint, self.chain_code, self.public_key, self.parent_fingerprint, self.private_key_hex]:
            i.setFont(monospace_font)
        for i in [self.depth, self.fingerprint, self.child_index, self.chain_code, self.public_key,
                    self.parent_fingerprint, self.private_key_hex]:
            i.setReadOnly(True)
        self.is_private = QCheckBox('Private Key?')
        self.is_private.setEnabled(False)

        self.model = ExtKeyModel()
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.depth, ExtKeyModel.DEPTH)
        self.mapper.addMapping(self.fingerprint, ExtKeyModel.FPRINT)
        self.mapper.addMapping(self.child_index, ExtKeyModel.CHILD_NUM)
        self.mapper.addMapping(self.chain_code, ExtKeyModel.CHAINCODE)
        self.mapper.addMapping(self.public_key, ExtKeyModel.PUBKEY)
        self.mapper.addMapping(self.parent_fingerprint, ExtKeyModel.PARENT_FPRINT)
        self.mapper.addMapping(self.is_private, ExtKeyModel.IS_PRIVATE)
        self.mapper.addMapping(self.private_key_hex, ExtKeyModel.PRIVKEY)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow('Depth:', self.depth)
        form.addRow('Fingerprint:', self.fingerprint)
        form.addRow('Child Index:', self.child_index)
        form.addRow('Chain Code:', self.chain_code)
        form.addRow('Public Key:', self.public_key)
        form.addRow('Parent Fingerprint:', self.parent_fingerprint)
        form.addRow(self.is_private)
        form.addRow('Private Key:', self.private_key_hex)

        self.setLayout(form)

    def set_key(self, key):
        self.model.set_key(key)
        self.mapper.setCurrentIndex(0)

    def clear(self):
        self.model.clear()
        self.mapper.setCurrentIndex(0)

class Pycoin(BaseDock):

    tool_name = 'Pycoin'
    description = 'Pycoin interface.'
    category = Category.Key
    is_large = True

    @augmenter
    def item_types(self, *args):
        return ExtKeyItem

    @augmenter
    def item_actions(self, *args):
        return (
            ItemAction(self.tool_name, 'Extended Key', 'Deserialize', self.deserialize_item),
        )

    def create_layout(self):
        self.key_edit = QLineEdit()
        self.key_edit.setFont(monospace_font)
        self.key_edit.textChanged.connect(self.evaluate_key_input)
        self.handler.substitute_variables(self.key_edit)
        self.key_edit.setWhatsThis('Enter a base58-encoded extended key here. If you have a key stored in the Variables tool, you can enter the variable name preceded by "$", and the variable value will be substituted automatically.')
        self.invalid_key_label = QLabel('Invalid key.')
        self.invalid_key_label.setProperty('hasError', True)
        self.invalid_key_label.setVisible(False)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        form.addRow('Extended Key:', self.key_edit)

        vbox = QVBoxLayout()
        vbox.addLayout(form)
        vbox.addWidget(self.invalid_key_label)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_deserialize_tab(), 'Deserialize')
        self.tabs.addTab(self.create_subkeys_tab(), 'Subkeys')
        vbox.addWidget(self.tabs)

        return vbox

    def create_deserialize_tab(self):
        self.ext_key_widget = ExtKeyWidget()
        vbox = QVBoxLayout()
        vbox.addWidget(self.ext_key_widget, stretch=1)
        w = QWidget()
        w.setLayout(vbox)
        return w

    def create_subkeys_tab(self):
        subkey_desc = QLabel(''.join([
            'Subkey paths are denoted using numbers with slashes to indicate subchildren. Examples:\n',
            '- Subkey 4 of subkey 8 is "8/4"\n',
            '- Hardened subkey 2 of subkey 5 is "5/2h" or "5/2\'"']))
        subkey_desc.setWordWrap(True)

        self.subkey_path = QLineEdit()
        self.subkey_path.setFont(monospace_font)
        self.subkey_path.textChanged.connect(self.derive_child)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Subkey: '))
        hbox.addWidget(self.subkey_path, stretch=1)
        self.invalid_subkey_label = QLabel('Invalid subkey.')
        self.invalid_subkey_label.setProperty('hasError', True)
        self.invalid_subkey_label.setVisible(False)

        vbox = QVBoxLayout()
        vbox.addWidget(subkey_desc)
        vbox.addLayout(hbox)
        vbox.addWidget(self.invalid_subkey_label)

        self.subkey_widget = ExtKeyWidget()
        vbox.addWidget(self.subkey_widget, stretch=1)

        w = QWidget()
        w.setLayout(vbox)
        return w

    def evaluate_key_input(self, txt):
        self.ext_key_widget.clear()
        self.subkey_widget.clear()
        txt = str(txt)
        if not txt:
            return self.invalid_key_label.setVisible(False)
        # Variable substitution.
        elif txt.startswith('$'):
            return
        try:
            key = BIP32Node.from_hwif(txt)
        except Exception as e:
            self.invalid_key_label.setVisible(True)
        else:
            self.invalid_key_label.setVisible(False)
            self.ext_key_widget.set_key(key)
            self.derive_child()
        finally:
            self.ext_key_widget.mapper.setCurrentIndex(0)

    def derive_child(self):
        strkey = str(self.key_edit.text())
        subkey_path = str(self.subkey_path.text())
        subkey_path = subkey_path.replace("'", "H").replace("h", "H")

        # Don't clear if the user is typing a path.
        if subkey_path.endswith('/'):
            return

        self.subkey_widget.clear()
        if not strkey or not subkey_path:
            return

        try:
            ext_key = BIP32Node.from_hwif(strkey)
            result = ext_key.subkey_for_path(subkey_path)
        except Exception as e:
            self.invalid_subkey_label.setText(str(e))
            self.invalid_subkey_label.setVisible(True)
        else:
            self.invalid_subkey_label.setVisible(False)
            self.subkey_widget.set_key(result)
        finally:
            self.subkey_widget.mapper.setCurrentIndex(0)

    def deserialize_item(self, item):
        self.key_edit.setText(str(item))
        self.needsFocus.emit()
