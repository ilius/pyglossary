#!/usr/bin/env python3


import glob
import logging
import os
import re
import sys
from os.path import dirname, exists, isdir, join

from setuptools import setup
from setuptools.command.install import install

VERSION = "5.0.3"
log = logging.getLogger("root")
relRootDir = "share/pyglossary"


def getGitVersion(gitDir: str) -> str:
	import subprocess

	try:
		outputB, _err = subprocess.Popen(
			[
				"git",
				"--git-dir",
				gitDir,
				"describe",
				"--always",
			],
			stdout=subprocess.PIPE,
		).communicate()
	except Exception as e:
		sys.stderr.write(str(e) + "\n")
		return ""
	# if _err is None:
	return outputB.decode("utf-8").strip()


def getPipSafeVersion() -> str:
	gitDir = ".git"
	if isdir(gitDir):
		version = getGitVersion(gitDir)
		if version:
			return "-".join(version.split("-")[:2])
	return VERSION


class my_install(install):
	def run(self) -> None:
		install.run(self)
		if os.sep == "/":
			binPath = join(self.install_scripts, "pyglossary")
			log.info(f"creating script file {binPath!r}")
			if not exists(self.install_scripts):
				os.makedirs(self.install_scripts)
				# let it fail on wrong permissions.
			elif not isdir(self.install_scripts):
				raise OSError(
					"installation path already exists "
					f"but is not a directory: {self.install_scripts}",
				)
			open(binPath, "w", encoding="ascii").write("""#!/usr/bin/env -S python3 -O
import sys
from os.path import dirname
sys.path.insert(0, dirname(__file__))
from pyglossary.ui.main import main
main()""")
			os.chmod(binPath, 0o755)


root_data_file_names = [
	"about",
	"LICENSE",
	"_license-dialog",
	"Dockerfile",
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
		"ui/ui_web/*.py",
		"ui/ui_web/*.html",
		"ui/ui_web/*.ico",
		"ui/ui_web/*.css",
		"ui/ui_web/*.js",
		"xdxf/xdxf.xsl",
		"xdxf/*.py",
	]
	+ [
		# safest way found so far to include every resource of plugins
		# producing plugins/pkg/*, plugins/pkg/sub1/*, ... except .pyc/.pyo
		re.sub(
			rf"^.*?pyglossary{sep}(?=plugins)",
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
	version=getPipSafeVersion(),
	python_requires=">=3.10.0",
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
