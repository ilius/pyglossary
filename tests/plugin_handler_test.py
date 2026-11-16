from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.plugin_handler import PluginLoader


class TestDisabledPluginFromJson(unittest.TestCase):
	def setUp(self):
		self.tempDir = tempfile.mkdtemp()
		self.oldLoadedModules = PluginLoader.loadedModules
		PluginLoader.loadedModules = set()

	def tearDown(self):
		PluginLoader.loadedModules = self.oldLoadedModules
		shutil.rmtree(self.tempDir)

	def writePluginJson(self, moduleName: str, enable: bool) -> str:
		jsonPath = join(self.tempDir, "index.json")
		with open(jsonPath, "w", encoding="utf-8") as file:
			json.dump(
				[
					{
						"module": moduleName,
						"lname": moduleName,
						"name": moduleName,
						"description": moduleName,
						"extensions": [".tmp"],
						"singleFile": True,
						"optionsProp": {},
						"canRead": True,
						"canWrite": False,
						"enable": enable,
					},
				],
				file,
			)
		return jsonPath

	def test_disabled_plugin_not_imported_by_directory_scan(self):
		moduleName = "disabled_test_plugin"
		jsonPath = self.writePluginJson(moduleName, enable=False)
		pluginsDir = join(self.tempDir, "plugins")
		pluginDir = join(pluginsDir, moduleName)
		os.makedirs(pluginDir)
		markerPath = join(self.tempDir, "imported")
		with open(join(pluginDir, "__init__.py"), "w", encoding="utf-8") as file:
			file.write(
				"from pathlib import Path\n"
				f"Path({markerPath!r}).write_text('imported')\n",
			)

		PluginLoader.loadPluginsFromJson(jsonPath, skipDisabled=True)
		plugins = PluginLoader.loadPlugins(pluginsDir, skipDisabled=True)

		self.assertEqual(plugins, [])
		self.assertFalse(
			os.path.exists(markerPath),
			"disabled plugin from JSON should not be imported again",
		)


if __name__ == "__main__":
	unittest.main()
