# Slob file writer (pyglossary)
from __future__ import annotations

import encodings
import operator
import os
import pickle
import sys
import tempfile
from builtins import open as fopen
from collections.abc import Callable
from datetime import UTC, datetime
from os.path import isdir
from struct import pack
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, NamedTuple, Self, cast

if TYPE_CHECKING:
	from types import TracebackType

from uuid import uuid4

import icu  # type: ignore

from ._blob import Blob
from ._collate import IDENTICAL, sortkey
from ._compressions import COMPRESSIONS
from ._constants import (
	DEFAULT_COMPRESSION,
	MAGIC,
	MAX_BIN_ITEM_COUNT,
	MAX_LARGE_BYTE_STRING_LEN,
	MAX_TEXT_LEN,
	MAX_TINY_TEXT_LEN,
	U_CHAR,
	U_INT_SIZE,
	U_LONG_LONG_SIZE,
	UTF8,
)
from ._exceptions import UnknownCompression, UnknownEncoding
from ._item_lists import BinMemWriter, RefList
from ._multifile import MultiFileReader
from ._struct import StructWriter
from ._types import Ref


class WriterEvent(NamedTuple):
	name: str
	data: object


class Writer:
	def __init__(  # noqa: PLR0913
		self,
		filename: str,
		workdir: str | None = None,
		encoding: str = UTF8,
		compression: str | None = DEFAULT_COMPRESSION,
		min_bin_size: int = 512 * 1024,
		max_redirects: int = 5,
		observer: Callable[[WriterEvent], None] | None = None,
		version_info: bool = True,
	) -> None:
		self.filename = filename
		self.observer = observer
		if os.path.exists(self.filename):
			raise SystemExit(f"File {self.filename!r} already exists")

		with fopen(self.filename, "wb"):
			pass

		self.encoding = encoding

		if encodings.search_function(self.encoding) is None:
			raise UnknownEncoding(self.encoding)

		self.workdir = workdir

		self.tmpdir = tmpdir = tempfile.TemporaryDirectory(
			prefix=f"{os.path.basename(filename)}-",
			dir=workdir,
		)

		self.f_ref_positions = self._wbfopen("ref-positions")
		self.f_store_positions = self._wbfopen("store-positions")
		self.f_refs = self._wbfopen("refs")
		self.f_store = self._wbfopen("store")

		self.max_redirects = max_redirects
		if max_redirects:
			self.aliases_path = os.path.join(tmpdir.name, "aliases")
			self.f_aliases = Writer(
				self.aliases_path,
				workdir=tmpdir.name,
				max_redirects=0,
				compression=None,
				version_info=False,
			)

		if compression is None:
			compression = ""
		if compression not in COMPRESSIONS:
			raise UnknownCompression(compression)

		self.compress = COMPRESSIONS[compression].compress

		self.compression = compression
		self.content_types: dict[str, int] = {}

		self.min_bin_size = min_bin_size

		self.current_bin: BinMemWriter | None = None

		created_at = os.getenv("SLOB_TIMESTAMP") or datetime.now(UTC).isoformat()

		self.blob_count = 0
		self.ref_count = 0
		self.bin_count = 0
		self._tags = {
			"created.at": created_at,
		}
		if version_info:
			self._tags.update(
				{
					"version.python": sys.version.replace("\n", " "),
					"version.pyicu": icu.VERSION,
					"version.icu": icu.ICU_VERSION,
				},
			)
		self.tags = MappingProxyType(self._tags)

	def _wbfopen(self, name: str) -> StructWriter:
		return StructWriter(
			fopen(os.path.join(self.tmpdir.name, name), "wb"),
			encoding=self.encoding,
		)

	def tag(self, name: str, value: str = "") -> None:
		if len(name.encode(self.encoding)) > MAX_TINY_TEXT_LEN:
			self._fire_event("tag_name_too_long", (name, value))
			return

		if len(value.encode(self.encoding)) > MAX_TINY_TEXT_LEN:
			self._fire_event("tag_value_too_long", (name, value))
			value = ""

		self._tags[name] = value

	@staticmethod
	def key_is_too_long(actual_key: str, fragment: str) -> bool:
		return len(actual_key) > MAX_TEXT_LEN or len(fragment) > MAX_TINY_TEXT_LEN

	@staticmethod
	def _split_key(
		key: str | tuple[str, str],
	) -> tuple[str, str]:
		if isinstance(key, str):
			actual_key = key
			fragment = ""
		else:
			actual_key, fragment = key
		return actual_key, fragment

	def add(
		self,
		blob: bytes,
		*keys: str,
		content_type: str = "",
	) -> None:
		if len(blob) > MAX_LARGE_BYTE_STRING_LEN:
			self._fire_event("content_too_long", blob)
			return

		if len(content_type) > MAX_TEXT_LEN:
			self._fire_event("content_type_too_long", content_type)
			return

		actual_keys = []

		for key in keys:
			actual_key, fragment = self._split_key(key)
			if self.key_is_too_long(actual_key, fragment):
				self._fire_event("key_too_long", key)
			else:
				actual_keys.append((actual_key, fragment))

		if not actual_keys:
			return

		current_bin = self.current_bin

		if current_bin is None:
			current_bin = self.current_bin = BinMemWriter()
			self.bin_count += 1

		if content_type not in self.content_types:
			self.content_types[content_type] = len(self.content_types)

		current_bin.add(self.content_types[content_type], blob)
		self.blob_count += 1
		bin_item_index = len(current_bin) - 1
		bin_index = self.bin_count - 1

		for actual_key, fragment in actual_keys:
			self._write_ref(actual_key, bin_index, bin_item_index, fragment)

		if (
			current_bin.current_offset > self.min_bin_size
			or len(current_bin) == MAX_BIN_ITEM_COUNT
		):
			self._write_current_bin()

	def add_alias(self, key: str, target_key: str) -> None:
		if not self.max_redirects:
			raise NotImplementedError
		if self.key_is_too_long(*self._split_key(key)):
			self._fire_event("alias_too_long", key)
			return
		if self.key_is_too_long(*self._split_key(target_key)):
			self._fire_event("alias_target_too_long", target_key)
			return
		self.f_aliases.add(pickle.dumps(target_key), key)

	def _fire_event(
		self,
		name: str,
		data: object = None,
	) -> None:
		if self.observer:
			self.observer(WriterEvent(name, data))

	def _write_current_bin(self) -> None:
		current_bin = self.current_bin
		if current_bin is None:
			return
		self.f_store_positions.write_long(self.f_store.tell())
		current_bin.finalize(
			self.f_store._file,
			self.compress,
		)
		self.current_bin = None

	def _write_ref(
		self,
		key: str,
		bin_index: int,
		item_index: int,
		fragment: str = "",
	) -> None:
		self.f_ref_positions.write_long(self.f_refs.tell())
		self.f_refs.write_text(key)
		self.f_refs.write_int(bin_index)
		self.f_refs.write_short(item_index)
		self.f_refs.write_tiny_text(fragment)
		self.ref_count += 1

	def _sort(self) -> None:
		self._fire_event("begin_sort")
		f_ref_positions_sorted = self._wbfopen("ref-positions-sorted")
		self.f_refs.flush()
		self.f_ref_positions.close()
		with MultiFileReader(self.f_ref_positions.name, self.f_refs.name) as f:
			ref_list = RefList(f, self.encoding, count=self.ref_count)
			sortkey_func = sortkey(IDENTICAL)
			for i in sorted(
				range(len(ref_list)),
				key=lambda j: sortkey_func(ref_list[j].key),
			):
				ref_pos = ref_list.pos(i)
				f_ref_positions_sorted.write_long(ref_pos)
		f_ref_positions_sorted.close()
		os.remove(self.f_ref_positions.name)
		os.rename(f_ref_positions_sorted.name, self.f_ref_positions.name)
		self.f_ref_positions = StructWriter(
			fopen(self.f_ref_positions.name, "ab"),
			encoding=self.encoding,
		)
		self._fire_event("end_sort")

	def _resolve_aliases(self) -> None:  # noqa: PLR0912, C901
		from ._slob_obj import Slob

		self._fire_event("begin_resolve_aliases")
		self.f_aliases.finalize()

		def read_key_frag(item: Blob, default_fragment: str) -> tuple[str, str]:
			key_frag = pickle.loads(item.content)
			if isinstance(key_frag, str):
				return key_frag, default_fragment
			to_key, fragment = key_frag
			return to_key, fragment

		with MultiFileReader(
			self.f_ref_positions.name,
			self.f_refs.name,
		) as f_ref_list:
			ref_list = RefList(f_ref_list, self.encoding, count=self.ref_count)
			ref_dict = ref_list.as_dict()
			with Slob(self.aliases_path) as aliasesSlob:
				aliases = aliasesSlob.as_dict()
				path = os.path.join(self.tmpdir.name, "resolved-aliases")
				alias_writer = Writer(
					path,
					workdir=self.tmpdir.name,
					max_redirects=0,
					compression=None,
					version_info=False,
				)

				for item in aliasesSlob:
					from_key = item.key
					keys = set()
					keys.add(from_key)
					to_key, fragment = read_key_frag(item, item.fragment)
					count = 0
					while count <= self.max_redirects:
						try:
							alias_item = next(aliases[to_key])
						except StopIteration:
							break
						assert isinstance(alias_item, Blob)
						orig_to_key = to_key
						to_key, fragment = read_key_frag(
							alias_item,
							fragment,
						)
						count += 1
						keys.add(orig_to_key)
					if count > self.max_redirects:
						self._fire_event("too_many_redirects", from_key)
					target_ref: Ref
					try:
						target_ref = cast("Ref", next(ref_dict[to_key]))
					except StopIteration:
						self._fire_event("alias_target_not_found", to_key)
					else:
						for key in keys:
							ref = Ref(
								key=key,
								bin_index=target_ref.bin_index,
								item_index=target_ref.item_index,
								fragment=target_ref.fragment or fragment,
							)
							alias_writer.add(pickle.dumps(ref), key)

				alias_writer.finalize()

		with Slob(path) as resolved_aliases_reader:
			previous = None
			targets = set()

			for item in resolved_aliases_reader:
				ref = pickle.loads(item.content)
				if previous is not None and ref.key != previous.key:
					for bin_index, item_index, fragment in sorted(targets):
						self._write_ref(previous.key, bin_index, item_index, fragment)
					targets.clear()
				targets.add((ref.bin_index, ref.item_index, ref.fragment))
				previous = ref

			if targets:
				assert previous is not None
				for bin_index, item_index, fragment in sorted(targets):
					self._write_ref(previous.key, bin_index, item_index, fragment)

		self._sort()
		self._fire_event("end_resolve_aliases")

	def finalize(self) -> None:
		self._fire_event("begin_finalize")
		if self.current_bin is not None:
			self._write_current_bin()

		self._sort()
		if self.max_redirects:
			self._resolve_aliases()

		files = (
			self.f_ref_positions,
			self.f_refs,
			self.f_store_positions,
			self.f_store,
		)
		for f in files:
			f.close()

		buf_size = 10 * 1024 * 1024

		def write_tags(tags: MappingProxyType[str, Any], f: StructWriter) -> None:
			f.write(pack(U_CHAR, len(tags)))
			for key, value in tags.items():
				f.write_tiny_text(key)
				f.write_tiny_text(value, editable=True)

		with fopen(self.filename, mode="wb") as output_file:
			out = StructWriter(output_file, self.encoding)
			out.write(MAGIC)
			out.write(uuid4().bytes)
			out.write_tiny_text(self.encoding, encoding=UTF8)
			out.write_tiny_text(self.compression)

			write_tags(self.tags, out)

			def write_content_types(
				content_types: dict[str, int],
				f: StructWriter,
			) -> None:
				count = len(content_types)
				f.write(pack(U_CHAR, count))
				types = sorted(content_types.items(), key=operator.itemgetter(1))
				for content_type, _ in types:
					f.write_text(content_type)

			write_content_types(self.content_types, out)

			out.write_int(self.blob_count)
			store_offset = (
				out.tell()
				+ U_LONG_LONG_SIZE
				+ U_LONG_LONG_SIZE
				+ U_INT_SIZE
				+ os.stat(self.f_ref_positions.name).st_size
				+ os.stat(self.f_refs.name).st_size
			)
			out.write_long(store_offset)
			out.flush()

			file_size = out.tell() + U_LONG_LONG_SIZE + 2 * U_INT_SIZE
			file_size += sum(os.stat(f.name).st_size for f in files)
			out.write_long(file_size)

			def mv(src: StructWriter, out: StructWriter) -> None:
				fname = src.name
				self._fire_event("begin_move", fname)
				with fopen(fname, mode="rb") as f:
					while True:
						data = f.read(buf_size)
						if len(data) == 0:
							break
						out.write(data)
						out.flush()
				os.remove(fname)
				self._fire_event("end_move", fname)

			out.write_int(self.ref_count)
			mv(self.f_ref_positions, out)
			mv(self.f_refs, out)

			out.write_int(self.bin_count)
			mv(self.f_store_positions, out)
			mv(self.f_store, out)

		self.f_ref_positions = None  # type: ignore # noqa: PGH003
		self.f_refs = None  # type: ignore # noqa: PGH003
		self.f_store_positions = None  # type: ignore # noqa: PGH003
		self.f_store = None  # type: ignore # noqa: PGH003

		self.tmpdir.cleanup()
		self._fire_event("end_finalize")

	def size_data(self) -> int:
		files = (
			self.f_ref_positions,
			self.f_refs,
			self.f_store_positions,
			self.f_store,
		)
		return sum(os.stat(f.name).st_size for f in files)

	def __enter__(self) -> Self:
		return self

	def close(self) -> None:
		for file in (
			self.f_ref_positions,
			self.f_refs,
			self.f_store_positions,
			self.f_store,
		):
			if file is None:
				continue
			self._fire_event("WARNING: closing without finalize()")
			try:
				file.close()
			except Exception:
				pass
		if self.tmpdir and isdir(self.tmpdir.name):
			self.tmpdir.cleanup()
		self.tmpdir = None  # type: ignore # noqa: PGH003

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_val: BaseException | None,
		exc_tb: TracebackType | None,
	) -> None:
		self.close()
