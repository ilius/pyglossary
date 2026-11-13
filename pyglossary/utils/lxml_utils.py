"""
Helpers for streaming lxml trees.

Contains the sibling-cleanup helper used by ``iterparse`` based readers to
release elements that have already been processed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.stubs.lxml_types import Element


__all__ = ["drop_previous_siblings"]


def drop_previous_siblings(elem: Element) -> None:
	"""Delete all preceding siblings of an element to free memory."""
	parent = elem.getparent()
	if parent is None:
		return
	while elem.getprevious() is not None:
		del parent[0]
