# -*- coding: utf-8 -*-
# dependency.py
#
# Copyright © 2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from typing import List

from pyglossary.glossary import Glossary

# Glossary.formatsDepends[format] == depends

# reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
# ^ this takes about 3 seconds
# installed_packages = set(r.decode().split('==')[0] for r in reqs.split())

try:
	ModuleNotFoundError
except NameError:
	ModuleNotFoundError = ImportError

def checkFormatDepends(name: str) -> List[str]:
	"returns the list of uninstalled dependencies"
	depends = Glossary.formatsDepends[name]
	if not depends:
		return []
	uninstalled = []
	for moduleName, pkgName in depends.items():
		try:
			__import__(moduleName)
		except ModuleNotFoundError:
			uninstalled.append(pkgName)
	return uninstalled

