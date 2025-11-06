# -*- coding: utf-8 -*-
#
# Copyright © 2016 ivan tkachenko me@ratijas.tk
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

"""extended indexes generation with respect to source language."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence

__all__ = ["languages"]

languages: dict[str, Callable[[Sequence[str], str], set[str]]] = {}

# submodules must register languages by adding (language name -> function)
# pairs to the mapping.

# function must follow signature below:
# 	:param titles: flat iterable of title and altenrative titles
# 	:param content: cleaned entry content
# 	:return: iterable of indexes (str).

import pyglossary.plugins.appledict.indexes.ru  # noqa: F401
import pyglossary.plugins.appledict.indexes.zh  # noqa: F401
