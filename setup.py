#!/usr/bin/env python3


import glob
import logging
import os
import re
from os.path import dirname, exists, isdir, join

from setuptools import setup
from setuptools.command.install import install

from pyglossary.core import VERSION

log = logging.getLogger("root")
relRootDir = "share/pyglossary"


class my_install(install):
	def run(self):
		install.run(self)
		if os.sep == "/":
			binPath = join(self.install_scripts, "pyglossary")
			log.info(f"creating script file {binPath!r}")
			if not exists(self.install_scripts):
				os.makedirs(self.install_scripts)
				# let it fail on wrong permissions.
			else:
				if not isdir(self.install_scripts):
					raise OSError(
						"installation path already exists "
						f"but is not a directory: {self.install_scripts}",
					)
			open(binPath, "w").write("""#!/usr/bin/env python3
import sys
from os.path import dirname
sys.path.insert(0, dirname(__file__))
from pyglossary.ui.main import main
main()""")
			os.chmod(binPath, 0o755)


root_data_file_names = [
	"about",
	"license.txt",
	"license-dialog",
	"Dockerfile",
	"pyglossary.pyw",
	"pyproject.toml",
	"help",
	"AUTHORS",
	"config.json",
]

sep = "\\\\" if os.sep == "\\" else os.sep

package_data = {
	"": root_data_file_names,
	"plugins-meta": [
		"index.json",
		"tools/*",
	],
	"pyglossary": [
		"*.py",
		"xdxf.xsl",
		"res/*",
		"plugins/*",
		"langs/*",
		"plugin_lib/*.py",
		"plugin_lib/py*/*.py",
		"sort_modules/*.py",
		"ui/*.py",
		"ui/progressbar/*.py",
		"ui/gtk3_utils/*.py",
		"ui/gtk4_utils/*.py",
		"ui/tools/*.py",
		"ui/wcwidth/*.py",
		"xdxf/xdxf.xsl",
		"xdxf/*.py",
	] + [
		# safest way found so far to include every resource of plugins
		# producing plugins/pkg/*, plugins/pkg/sub1/*, ... except .pyc/.pyo
		re.sub(
			fr"^.*?pyglossary{sep}(?=plugins)",
			"",
			join(dirpath, fname),
		)
		for top in glob.glob(
			join(dirname(__file__), "pyglossary", "plugins"),
		)
		for dirpath, _, files in os.walk(top)
		for fname in files
		if not fname.endswith((".pyc", ".pyo"))
	],
}


with open("README.md", encoding="utf-8") as fh:
	long_description = fh.read()

setup(
	name="pyglossary",
	version=VERSION,
	python_requires=">=3.9.0",
	cmdclass={
		"install": my_install,
	},
	description="A tool for converting dictionary files aka glossaries.",
	long_description_content_type="text/markdown",
	long_description=long_description,
	author="Saeed Rasooli",
	author_email="saeed.gnu@gmail.com",
	license="GPLv3+",
	url="https://github.com/ilius/pyglossary",
	packages=[
		"pyglossary",
	],
	entry_points={
		"console_scripts": [
			"pyglossary = pyglossary.ui.main:main",
		],
	},
	package_data=package_data,
	# data_files is deprecated, but without it
	# `pip install --user` does not work, tested with pip 22.0.2
	data_files=[
		(relRootDir, root_data_file_names),
		(f"{relRootDir}/plugins-meta", ["plugins-meta/index.json"]),
		(f"{relRootDir}/res", glob.glob("res/*")),
	],
	extras_require={
		"full": [
			"lxml",
			"beautifulsoup4",
			"PyICU",
			"PyYAML",
			"marisa-trie",
			"libzim",
			"python-lzo",
			"html5lib",
		],
	},
)
