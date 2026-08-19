# Packed bin/item index helpers for slob (pyglossary)
"""
Packed integer helpers for SLOB on-disk indexes.

Merges and splits 16-bit index components stored in combined integer fields
inside SLOB binary structures.
"""

from __future__ import annotations

__all__ = ["meld_ints", "unmeld_ints"]


def meld_ints(a: int, b: int) -> int:
	return (a << 16) | b


def unmeld_ints(c: int) -> tuple[int, int]:
	bstr = bin(c).lstrip("0b").zfill(48)
	a, b = bstr[-48:-16], bstr[-16:]
	return int(a, 2), int(b, 2)
