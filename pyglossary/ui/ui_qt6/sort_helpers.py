# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

"""
Sort-key UI helpers for the Qt 6 backend.

Populates sort-module combo boxes and wires locale collation options to glossary
config.
"""

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
