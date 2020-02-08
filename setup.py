#!/usr/bin/env python3

try:
	import py2exe
except ImportError:
	py2exe = None

import glob
import sys
import os
from os.path import join, dirname, exists, isdir
import re
import logging

import setuptools
from distutils.core import setup
from distutils.command.install import install

from pyglossary.glossary import VERSION

log = logging.getLogger("root")
relRootDir = "share/pyglossary"


class my_install(install):
	def run(self):
		install.run(self)
		if os.sep == "/":
			binPath = join(self.install_scripts, "pyglossary")
			log.info("creating script file \"%s\"", binPath)
			if not exists(self.install_scripts):
				os.makedirs(self.install_scripts)
				# let it fail on wrong permissions.
			else:
				if not isdir(self.install_scripts):
					raise OSError(
						"installation path already exists " +
						"but is not a directory: %s" % self.install_scripts
					)
			open(binPath, "w").write(
				join(self.install_data, relRootDir, "main.py") +
				" \"$@\""  # pass options from command line
			)
			os.chmod(binPath, 0o755)


data_files = [
	(relRootDir, [
		"about",
		"license.txt",
		"license-dialog",
		"help",
		"main.py",
		"pyglossary.pyw",
		"AUTHORS",
		"config.json",
	]),
	(relRootDir+"/ui", glob.glob("ui/*.py")),
	(relRootDir+"/ui/glade", glob.glob("ui/glade/*")),
	(relRootDir+"/ui/gtk3_utils", glob.glob("ui/gtk3_utils/*.py")),
	(relRootDir+"/res", glob.glob("res/*")),
	("share/doc/pyglossary", []),
	("share/doc/pyglossary/non-gui_examples",
		glob.glob("doc/non-gui_examples/*")),
	("share/doc/pyglossary/Babylon", glob.glob("doc/Babylon/*")),
	("share/doc/pyglossary/DSL", glob.glob("doc/DSL/*")),
	("share/doc/pyglossary/Octopus MDict", glob.glob("doc/Octopus MDict/*")),
	("share/applications", ["pyglossary.desktop"]),
	("share/pixmaps", ["res/pyglossary.png"]),
]


def files(folder):
	for path in glob.glob(folder+"/*"):
		if os.path.isfile(path):
			yield path

if py2exe:
	py2exeoptions = {
		"script_args": ["py2exe"],
		"bundle_files": 1,
		"windows": [
			{
				"script": "main.py", # or pyglossary.pyw ?
				"icon_resources": [
					(1, "res/pyglossary.ico"),
				],
			},
		],
		"zipfile": None,
		"options": {
			"py2exe": {
				"packages": [
					"pyglossary",
					"ui.ui_tk",
					# "ui.ui_gtk",
					# "BeautifulSoup",
					# "xml",
					"Tkinter", "tkFileDialog", "Tix",
					# "gtk", "glib", "gobject",
				],
			},
		},
	}
	data_files = [
		("tcl/tix8.1", files(join(sys.prefix, "tcl", "tix8.4.3"))),
		("tcl/tix8.1/bitmaps",
			files(join(sys.prefix, "tcl", "tix8.4.3", "bitmaps"))),
		("tcl/tix8.1/pref",
			files(join(sys.prefix, "tcl", "tix8.4.3", "pref"))),
		("tcl/tcl8.1/init.tcl",
			[join(sys.prefix, "tcl", "tix8.4.3", "init.tcl")]),
		("", ["about", "license-dialog", "help"]),
		("ui", glob.glob("ui/*.py")),
		("ui/glade", glob.glob("ui/glade/*")),
		("res", glob.glob("res/*")),
		("plugins", glob.glob("pyglossary/plugins/*")),
		("plugin_lib", glob.glob("pyglossary/plugin_lib/*")),
		("doc/pyglossary", ["doc/bgl_structure.svgz", ]),
		("doc/pyglossary/non-gui_examples",
			glob.glob("doc/non-gui_examples/*")),
	]
	for pyVer in ("34", "35", "36"):
		relPath = "plugin_lib/py%s" % pyVer
		data_files.append((
			relPath,
			glob.glob("pyglossary/" + relPath + "/*.py",
		)))
else:
	py2exeoptions = {}

with open("README.md", "r") as fh:
	long_description = fh.read()

setup(
	name="pyglossary",
	version=VERSION,
	cmdclass={
		"install": my_install,
	},
	description="A tool for workig with dictionary databases",
	long_description_content_type="text/markdown",
	long_description=long_description,
	author="Saeed Rasooli",
	author_email="saeed.gnu@gmail.com",
	license="GPLv3+",
	url="https://github.com/ilius/pyglossary",
	scripts=[
		# "main.py",
	],
	packages=[
		"pyglossary",
	],
	package_data={
		"pyglossary": [
			"plugins/*.py",
			"plugin_lib/*.py",
			"plugin_lib/py*/*.py",
		] + [
			# safest way found so far to include every resource of plugins
			# producing plugins/pkg/*, plugins/pkg/sub1/*, ... except .pyc/.pyo
			re.sub(
				r"^.*?pyglossary%s(?=plugins)" % ("\\\\" if os.sep == "\\" else os.sep),
				"",
				join(dirpath, f),
			)
			for top in glob.glob(
				join(dirname(__file__), "pyglossary", "plugins")
			)
			for dirpath, _, files in os.walk(top)
			for f in files
			if not (f.endswith(".pyc") or f.endswith(".pyo"))
		],
	},
	data_files=data_files,
	**py2exeoptions
)
