# -*- coding: utf-8 -*-
from __future__ import annotations

__all__ = [
	"HASH_SET_CAPACITY_FACTOR",
	"HASH_SET_INIT",
	"HASH_SET_INIT2",
	"LINKED_HASH_SET_INIT",
	"EntryIndexTuple",
	"IndexEntryType",
]


HASH_SET_INIT = (
	b"\xac\xed"  # magic
	b"\x00\x05"  # version
	b"\x73"  # object
	b"\x72"  # class
	# Java String "java.util.HashSet":
	b"\x00\x11\x6a\x61\x76\x61\x2e\x75\x74\x69"
	b"\x6c\x2e\x48\x61\x73\x68\x53\x65\x74"
)
"""First part of Java serialization of java.util.HashSet"""

HASH_SET_INIT2 = (
	# serialization ID:
	b"\xba\x44\x85\x95\x96\xb8\xb7\x34"
	b"\x03"  # flags: serialized, custom serialization function
	b"\x00\x00"  # fields count
	b"\x78"  # blockdata end
	b"\x70"  # null (superclass)
	b"\x77\x0c"  # blockdata short, 0xc bytes
)
"""Second part of Java serialization of java.util.HashSet"""

LINKED_HASH_SET_INIT = (
	(
		b"\xac\xed"  # magic
		b"\x00\x05"  # version
		b"\x73"  # object
		b"\x72"  # class
		# Java String "java.util.LinkedHashSet":
		b"\x00\x17\x6a\x61\x76\x61\x2e\x75\x74\x69"
		b"\x6c\x2e\x4c\x69\x6e\x6b\x65\x64"
		b"\x48\x61\x73\x68\x53\x65\x74"
		# serialization ID:
		b"\xd8\x6c\xd7\x5a\x95\xdd\x2a\x1e"
		b"\x02"  # flags
		b"\x00\x00"  # fields count
		b"\x78"  # blockdata end
		b"\x72"  # superclass (java.util.HashSet)
		b"\x00\x11\x6a\x61\x76\x61\x2e\x75\x74\x69"
		b"\x6c\x2e\x48\x61\x73\x68\x53\x65\x74"
	)
	+ HASH_SET_INIT2
)
"""Header of Java serialization of java.util.LinkedHashSet"""

HASH_SET_CAPACITY_FACTOR = 0.75
"""Capacity factor used to determine the hash set's capacity from its length"""


IndexEntryType = tuple[
	str,  # token
	int,  # start_index
	int,  # count
	str,  # token_norm
	list[int],  # html_indices
]


EntryIndexTuple = tuple[
	str,  # short_name
	str,  # long_name
	str,  # iso
	str,  # normalizer_rules
	bool,  # swap_flag
	int,  # main_token_count
	list[IndexEntryType],  # index_entries
	list[str],  # stop_list,
	list[tuple[int, int]],  # rows
]
