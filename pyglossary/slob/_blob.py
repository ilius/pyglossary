# Blob and key-indexed views for slob (pyglossary)
from __future__ import annotations

from bisect import bisect_left
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Protocol

from ._collate import sortkey
from ._types import Ref

if TYPE_CHECKING:

	class MiniSequence[T](Protocol):
		def __getitem__(self, s: int) -> T: ...
		def __len__(self) -> int: ...


class Blob:
	def __init__(  # noqa: PLR0913
		self,
		content_id: int,
		key: str,
		fragment: str,
		read_content_type_func: Callable[[], str],
		read_func: Callable[[], bytes],
	) -> None:
		self._content_id = content_id
		self._key = key
		self._fragment = fragment
		self._read_content_type = read_content_type_func
		self._read = read_func

	@property
	def identity(self) -> int:
		return self._content_id

	@property
	def key(self) -> str:
		return self._key

	@property
	def fragment(self) -> str:
		return self._fragment

	@property
	def content_type(self) -> str:
		return self._read_content_type()

	@property
	def content(self) -> bytes:
		return self._read()

	def __str__(self) -> str:
		return self.key

	def __repr__(self) -> str:
		return f"<{self.__class__.__module__}.{self.__class__.__name__} {self.key}>"


class KeydItemDict[T: (Blob, Ref)]:
	def __init__(
		self,
		blobs: MiniSequence[T],
		strength: int,
		maxlength: int | None = None,
	) -> None:
		self.blobs: MiniSequence[T] = blobs
		self.sortkey = sortkey(strength, maxlength=maxlength)

	def __len__(self) -> int:
		return len(self.blobs)

	def __getitem__(self, key: str) -> Iterator[Blob | Ref]:
		blobs = self.blobs
		key_as_sk = self.sortkey(key)
		i = bisect_left(
			blobs,
			key_as_sk,
			key=lambda blob: self.sortkey(blob.key),
		)
		if i == len(blobs):
			return
		while i < len(blobs):
			if self.sortkey(blobs[i].key) == key_as_sk:
				yield blobs[i]
			else:
				break
			i += 1

	def __contains__(self, key: str) -> bool:
		try:
			next(self[key])
		except StopIteration:
			return False
		return True
