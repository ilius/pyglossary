# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from pyglossary.sort_keys import namedSortKeyList

__all__ = [
	"SORT_KEY_DESC_BY_NAME",
	"SORT_KEY_DESC_LIST",
	"SORT_KEY_NAME_BY_DESC",
]

SORT_KEY_NAME_BY_DESC = {sk.desc: sk.name for sk in namedSortKeyList}
SORT_KEY_DESC_BY_NAME = {sk.name: sk.desc for sk in namedSortKeyList}
SORT_KEY_DESC_LIST = [sk.desc for sk in namedSortKeyList]
