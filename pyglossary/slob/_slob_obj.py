# Slob reader object (pyglossary)
from __future__ import annotations

from collections.abc import Sequence
from functools import cache, lru_cache
from types import MappingProxyType
from typing import TYPE_CHECKING, Self

from ._binary import meld_ints, unmeld_ints
from ._blob import Blob, KeydItemDict
from ._collate import TERTIARY
from ._compressions import COMPRESSIONS
from ._exceptions import FileFormatException, IncorrectFileSize
from ._header import read_header
from ._item_lists import RefList, Store
from ._multifile import MultiFileReader

if TYPE_CHECKING:
	from collections.abc import Iterator
	from types import TracebackType


class Slob:
	def __init__(
		self,
		*filenames: str,
	) -> None:
		self._f = MultiFileReader(*filenames)

		try:
			self._header = read_header(self._f)
			if self._f.size != self._header.size:
				raise IncorrectFileSize(
					f"File size should be {self._header.size}, "
					f"{self._f.size} bytes found",
				)
		except FileFormatException:
			self._f.close()
			raise

		self._refs = RefList(
			self._f,
			self._header.encoding,
			offset=self._header.refs_offset,
		)

		self._g = MultiFileReader(*filenames)
		self._store = Store(
			self._g,
			self._header.store_offset,
			COMPRESSIONS[self._header.compression].decompress,
			self._header.content_types,
		)

	def __enter__(self) -> Self:
		return self

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_val: BaseException | None,
		exc_tb: TracebackType | None,
	) -> None:
		self.close()

	@property
	def identity(self) -> str:
		return self._header.uuid.hex

	@property
	def content_types(self) -> Sequence[str]:
		return self._header.content_types

	@property
	def tags(self) -> MappingProxyType[str, str]:
		return self._header.tags

	@property
	def blob_count(self) -> int:
		return self._header.blob_count

	@property
	def compression(self) -> str:
		return self._header.compression

	@property
	def encoding(self) -> str:
		return self._header.encoding

	def __len__(self) -> int:
		return len(self._refs)

	def __getitem__(self, i: int) -> Blob:
		return self.getBlobByIndex(i)

	def __iter__(self) -> Iterator[Blob]:
		for i in range(len(self._refs)):
			yield self.getBlobByIndex(i)

	def count(self) -> int:
		raise NotImplementedError

	def index(self, x: Blob) -> int:
		raise NotImplementedError

	def getBlobByIndex(self, i: int) -> Blob:
		ref = self._refs[i]

		def read_func() -> bytes:
			return self._store.get(ref.bin_index, ref.item_index)[1]

		read_func = lru_cache(maxsize=None)(read_func)

		def read_content_type_func() -> str:
			return self._store.content_type(ref.bin_index, ref.item_index)

		content_id = meld_ints(ref.bin_index, ref.item_index)
		return Blob(
			content_id=content_id,
			key=ref.key,
			fragment=ref.fragment,
			read_content_type_func=read_content_type_func,
			read_func=read_func,
		)

	def get(self, blob_id: int) -> tuple[str, bytes]:
		"""Returns (content_type: str, content: bytes)."""
		bin_index, bin_item_index = unmeld_ints(blob_id)
		return self._store.get(bin_index, bin_item_index)

	@cache
	def as_dict(
		self: Slob,
		strength: int = TERTIARY,
		maxlength: int | None = None,
	) -> KeydItemDict[Blob]:
		blobs = self
		return KeydItemDict(
			blobs,
			strength=strength,
			maxlength=maxlength,
		)

	def close(self) -> None:
		self._f.close()
		self._g.close()
