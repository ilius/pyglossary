# On-disk ref/store item lists for slob (pyglossary)
from __future__ import annotations

import io
from abc import abstractmethod
from collections.abc import Callable, Sequence
from functools import cache, lru_cache
from io import BufferedIOBase
from struct import calcsize, pack, unpack
from threading import RLock
from typing import TYPE_CHECKING, NamedTuple, cast

from ._blob import KeydItemDict
from ._collate import TERTIARY
from ._constants import U_CHAR, U_CHAR_SIZE, U_INT, U_LONG_LONG
from ._struct import StructReader
from ._types import Ref

if TYPE_CHECKING:
	from io import IOBase


class BinMemWriter:
	def __init__(self) -> None:
		self.content_type_ids: list[int] = []
		self.item_dir: list[bytes] = []
		self.items: list[bytes] = []
		self.current_offset = 0

	def add(self, content_type_id: int, blob_bytes: bytes) -> None:
		self.content_type_ids.append(content_type_id)
		self.item_dir.append(pack(U_INT, self.current_offset))
		length_and_bytes = pack(U_INT, len(blob_bytes)) + blob_bytes
		self.items.append(length_and_bytes)
		self.current_offset += len(length_and_bytes)

	def __len__(self) -> int:
		return len(self.item_dir)

	def finalize(
		self,
		fout: BufferedIOBase,
		compress: Callable[[bytes], bytes],
	) -> None:
		count = len(self)
		fout.write(pack(U_INT, count))
		fout.writelines(
			pack(U_CHAR, content_type_id) for content_type_id in self.content_type_ids
		)
		content = b"".join(self.item_dir + self.items)
		compressed = compress(content)
		fout.write(pack(U_INT, len(compressed)))
		fout.write(compressed)
		self.content_type_ids.clear()
		self.item_dir.clear()
		self.items.clear()


class ItemList[T]:
	def __init__(
		self,
		reader: StructReader,
		offset: int,
		count_or_spec: str | int,
		pos_spec: str,
	) -> None:
		self.lock = RLock()
		self.reader = reader
		reader.seek(offset)
		count: int
		if isinstance(count_or_spec, str):
			count_spec = count_or_spec
			count = unpack(count_spec, reader.read(calcsize(count_spec)))[0]
		elif isinstance(count_or_spec, int):
			count = count_or_spec
		else:
			raise TypeError(f"invalid {count_or_spec = }")
		self._count: int = count
		self.pos_offset = reader.tell()
		self.pos_spec = pos_spec
		self.pos_size = calcsize(pos_spec)
		self.data_offset = self.pos_offset + self.pos_size * count

	def __len__(self) -> int:
		return self._count

	def pos(self, i: int) -> int:
		with self.lock:
			self.reader.seek(self.pos_offset + self.pos_size * i)
			return unpack(self.pos_spec, self.reader.read(self.pos_size))[0]

	def read(self, pos: int) -> T:
		with self.lock:
			self.reader.seek(self.data_offset + pos)
			return self._read_item()

	@abstractmethod
	def _read_item(self) -> T:
		pass

	def __getitem__(self, i: int) -> T:
		if i >= len(self) or i < 0:
			raise IndexError("index out of range")
		return self.read(self.pos(i))


class RefList(ItemList[Ref]):
	def __init__(
		self,
		f: IOBase,
		encoding: str,
		offset: int = 0,
		count: int | None = None,
	) -> None:
		super().__init__(
			reader=StructReader(f, encoding),
			offset=offset,
			count_or_spec=U_INT if count is None else count,
			pos_spec=U_LONG_LONG,
		)

	@lru_cache(maxsize=512)
	def __getitem__(
		self,
		i: int,
	) -> Ref:
		if i >= len(self) or i < 0:
			raise IndexError("index out of range")
		return cast("Ref", self.read(self.pos(i)))

	def _read_item(self) -> Ref:
		key = self.reader.read_text()
		bin_index = self.reader.read_int()
		item_index = self.reader.read_short()
		fragment = self.reader.read_tiny_text()
		return Ref(
			key=key,
			bin_index=bin_index,
			item_index=item_index,
			fragment=fragment,
		)

	@cache
	def as_dict(
		self: RefList,
		strength: int = TERTIARY,
		maxlength: int | None = None,
	) -> KeydItemDict[Ref]:
		refs = self
		return KeydItemDict(
			refs,
			strength=strength,
			maxlength=maxlength,
		)


class Bin(ItemList[bytes]):
	def __init__(
		self,
		count: int,
		bin_bytes: bytes,
	) -> None:
		super().__init__(
			reader=StructReader(io.BytesIO(bin_bytes)),
			offset=0,
			count_or_spec=count,
			pos_spec=U_INT,
		)

	def _read_item(self) -> bytes:
		content_len = self.reader.read_int()
		return self.reader.read(content_len)


class StoreItem(NamedTuple):
	content_type_ids: list[int]
	compressed_content: bytes


class Store(ItemList[StoreItem]):
	def __init__(
		self,
		file: IOBase,
		offset: int,
		decompress: Callable[[bytes], bytes],
		content_types: Sequence[str],
	) -> None:
		super().__init__(
			reader=StructReader(file),
			offset=offset,
			count_or_spec=U_INT,
			pos_spec=U_LONG_LONG,
		)
		self.decompress = decompress
		self.content_types = content_types

	@lru_cache(maxsize=32)
	def __getitem__(
		self,
		i: int,
	) -> StoreItem:
		if i >= len(self) or i < 0:
			raise IndexError("index out of range")
		return cast("StoreItem", self.read(self.pos(i)))

	def _read_item(self) -> StoreItem:
		bin_item_count = self.reader.read_int()
		packed_content_type_ids = self.reader.read(bin_item_count * U_CHAR_SIZE)
		content_type_ids = []
		for i in range(bin_item_count):
			content_type_id = unpack(U_CHAR, packed_content_type_ids[i : i + 1])[0]
			content_type_ids.append(content_type_id)
		content_length = self.reader.read_int()
		content = self.reader.read(content_length)
		return StoreItem(
			content_type_ids=content_type_ids,
			compressed_content=content,
		)

	def _content_type(
		self,
		bin_index: int,
		item_index: int,
	) -> tuple[str, StoreItem]:
		store_item = self[bin_index]
		content_type_id = store_item.content_type_ids[item_index]
		content_type = self.content_types[content_type_id]
		return content_type, store_item

	def content_type(
		self,
		bin_index: int,
		item_index: int,
	) -> str:
		return self._content_type(bin_index, item_index)[0]

	@lru_cache(maxsize=16)
	def _decompress(self, bin_index: int) -> bytes:
		store_item = self[bin_index]
		return self.decompress(store_item.compressed_content)

	def get(
		self,
		bin_index: int,
		item_index: int,
	) -> tuple[str, bytes]:
		content_type, store_item = self._content_type(bin_index, item_index)
		content = self._decompress(bin_index)
		count = len(store_item.content_type_ids)
		store_bin = Bin(count, content)
		content = store_bin[item_index]
		return (content_type, content)
