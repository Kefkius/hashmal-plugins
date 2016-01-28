from PyQt4.QtGui import *
from PyQt4.QtCore import *

import hashmal_lib
from hashmal_lib.plugins import BasePluginUI, Plugin, augmenter, Category

import explorers

def make_plugin():
    p = Plugin(CoinCodex)
    p.has_gui = False
    return p

class CoinCodex(BasePluginUI):
    tool_name = 'Coin Codex'
    description = 'Augments the Blockchain plugin with explorers for various coins.'
    category = Category.Data

    @augmenter
    def block_explorers(self, data):
        known_explorers = data.get('known_explorers')
        my_explorers = explorers.my_explorers

        known_explorers.update(my_explorers)

