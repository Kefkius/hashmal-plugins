import unittest, sys, __builtin__

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import Qt
from PyQt4.QtTest import QTest

from hashmal_lib.core import chainparams
from hashmal_lib.main_window import HashmalMain


__builtin__.use_local_modules = False

app = QApplication(sys.argv)

chainparams.set_to_preset('Bitcoin')

class TxAnalyzerTest(unittest.TestCase):
    def setUp(self):
        self.gui = HashmalMain(app)
        self.ui = self.gui.plugin_handler.get_plugin('Transaction Analyzer').ui
        self.params_changer = self.gui.settings_dialog.params_combo
        self._set_chainparams('Bitcoin')

    def _set_chainparams(self, name):
        chainparams.set_to_preset(name)
        self.gui.config.set_option('chainparams', name, do_save=False)
        self.params_changer.paramsChanged.emit()

    def test_input_view_headers(self):
        model = self.ui.tx_widget.inputs_tree.model
        view = self.ui.tx_widget.inputs_tree.view

        expected_fields = ['Hash', 'Index', 'Sig Script', 'Sequence']
        for i, expected in enumerate(expected_fields):
            self.assertEqual(expected, model.headerData(i, Qt.Horizontal))

        self.assertIsNot(self.gui.plugin_handler.get_plugin('Decred'), None, 'The "Decred" chainparams preset is not present.')
        # Change to Decred.
        self._set_chainparams('Decred')
        expected_fields = ['Hash', 'Index', 'Tree', 'Sequence', 'Value', 'Block Height', 'Block Index', 'Sig Script']
        for i, expected in enumerate(expected_fields):
            self.assertEqual(expected, model.headerData(i, Qt.Horizontal))

        # Change to Bitcoin again.
        self._set_chainparams('Bitcoin')
        expected_fields = ['Hash', 'Index', 'Sig Script', 'Sequence']
        for i, expected in enumerate(expected_fields):
            self.assertEqual(expected, model.headerData(i, Qt.Horizontal))

