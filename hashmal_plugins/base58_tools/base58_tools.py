from PyQt4.QtGui import *
from PyQt4.QtCore import *

from bitcoin import base58

from hashmal_lib.core.utils import is_hex, format_hex_string
from hashmal_lib.gui_utils import floated_buttons, Separator
from hashmal_lib.plugins import BaseDock, Plugin, augmenter, Category

def make_plugin():
    return Plugin(Base58Tools)


class Base58Tools(BaseDock):
    tool_name = 'Base58 Tools'
    description = 'Base58 Tools encodes and decodes base58 data.'
    is_large = False

    def create_layout(self):
        self.payload_edit = QPlainTextEdit()
        self.handler.substitute_variables(self.payload_edit)
        self.payload_edit.setToolTip('Hex data')
        self.payload_edit.setWhatsThis('Enter hex data that you want to base58-encode here.')
        self.encoded_edit = QPlainTextEdit()
        self.handler.substitute_variables(self.encoded_edit)
        self.encoded_edit.setToolTip('Base58 data')
        self.encoded_edit.setWhatsThis('Enter base58 data that you want to decode here.')

        for i in [self.payload_edit, self.encoded_edit]:
            i.setTabChangesFocus(True)

        self.encode_button = QPushButton('Encode')
        self.encode_button.setWhatsThis('Click this to base58-encode the above data.')
        self.encode_button.clicked.connect(self.encode_data)
        self.decode_button = QPushButton('Decode')
        self.decode_button.setWhatsThis('Click this to decode the above base58 data.')
        self.decode_button.clicked.connect(self.decode_data)

        encode_vbox = QVBoxLayout()
        encode_vbox.addWidget(self.payload_edit)
        encode_vbox.addLayout(floated_buttons([self.encode_button]))

        decode_vbox = QVBoxLayout()
        decode_vbox.addWidget(self.encoded_edit)
        decode_vbox.addLayout(floated_buttons([self.decode_button]))

        vbox = QVBoxLayout()
        vbox.addLayout(encode_vbox)
        vbox.addWidget(Separator())
        vbox.addLayout(decode_vbox)
        vbox.addStretch(1)

        return vbox

    def encode_data(self):
        payload = str(self.payload_edit.toPlainText())
        if not payload:
            self.error('No data was input.')

        if is_hex(payload):
            payload = format_hex_string(payload, with_prefix=False).decode('hex')

        try:
            msg = base58.encode(payload)
            self.encoded_edit.setPlainText(msg)
        except Exception as e:
            self.error(str(e))

    def decode_data(self):
        msg = str(self.encoded_edit.toPlainText())
        if not msg:
            self.error('No data was input.')

        try:
            payload = base58.decode(msg)
            self.payload_edit.setPlainText(payload.encode('hex'))
        except Exception as e:
            self.error(str(e))

