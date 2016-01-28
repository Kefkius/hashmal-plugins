#!/usr/bin/env python

from setuptools import setup, find_packages

plugin_entry_points = [
    'Coin Claimer = hashmal_plugins.coin_claimer.coin_claimer:make_plugin',
    'Coin Codex = hashmal_plugins.coin_codex.coin_codex:make_plugin',
    'Pycoin = hashmal_plugins.pycoin.hashmal_pycoin:make_plugin'
]

setup(
    name = 'Hashmal Plugins',
    version = '0.1.0',
    description = 'Plugins for Hashmal.',
    packages = find_packages(),
    entry_points = {
        'hashmal.plugin': plugin_entry_points,
    },
    test_suite = 'hashmal_plugins.tests'
)
