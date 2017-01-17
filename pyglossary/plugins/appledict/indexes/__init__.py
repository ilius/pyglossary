# -*- coding: utf-8 -*-
# appledict/indexes/__init__.py
#
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
"""
extended indexes generation with respect to source language.
"""

import os
import pkgutil

from pyglossary.plugins.formats_common import log

__all__ = ['languages', 'log']

languages = {}
"""
Dict[str, Callable[[Sequence[str], str], Sequence[str]]]

submodules must register languages by adding (language name -> function)
pairs to the mapping.

function must follow signature bellow:
	:param titles: flat iterable of title and altenrative titles
	:param content: cleaned entry content
	:return: iterable of indexes (str).

use
```
	from . import languages
	# or
	from appledict.indexes import languages
```
"""

here = os.path.dirname(os.path.abspath(__file__))

for _, module, _ in pkgutil.iter_modules([here]):
	try:
		__import__('%s.%s' % (__name__, module))
	except ImportError:
		log.exception(
			"error while importing indexes plugin %s" % module
		)
