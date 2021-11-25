#!/usr/bin/env python3

import glob
import sys
import os
from os.path import join, dirname, exists, isdir
import re
import logging

import setuptools
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
	"help",
	"AUTHORS",
	"config.json",
]


package_data = {
	"": root_data_file_names,
	"pyglossary": [
		"*.py",
		"xdxf.xsl",
		"res/*",
		"plugins/*.py",
		"langs/*",
		"plugin_lib/*.py",
		"plugin_lib/py*/*.py",
		"ui/*.py",
		"ui/progressbar/*.py",
		"ui/gtk3_utils/*.py",
		"ui/wcwidth/*.py",
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
}


def files(folder):
	for path in glob.glob(folder + "/*"):
		if os.path.isfile(path):
			yield path


with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setup(
	name="pyglossary",
	version=VERSION,
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
		'console_scripts': [
			'pyglossary = pyglossary.ui.main:main',
		],
	},
	package_data=package_data,
	# FIXME: data_files is deprecated, but without it
	# `pip install --user` does not work
	data_files=[
		(relRootDir, root_data_file_names),
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
		],
	},
)
