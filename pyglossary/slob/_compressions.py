# slob compression registry (pyglossary)
from __future__ import annotations

import typing
import warnings
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple, cast


class Compression(NamedTuple):
	compress: Callable[..., bytes]  # first arg: bytes
	decompress: Callable[[bytes], bytes]


class CompressionModule(typing.Protocol):
	@staticmethod
	def compress(data: bytes, compresslevel: int = 9) -> bytes:
		raise NotImplementedError

	@staticmethod
	def decompress(
		data: bytes,
		**kwargs: Mapping[str, Any],
	) -> bytes:
		raise NotImplementedError


def _load_bz2() -> CompressionModule:
	import bz2

	return cast("CompressionModule", bz2)


def _load_zlib() -> CompressionModule:
	import zlib

	return cast("CompressionModule", zlib)


_basicCompressionModules: dict[str, Callable[[], CompressionModule]] = {
	"bz2": _load_bz2,
	"zlib": _load_zlib,
}


def _init_compressions() -> dict[str, Compression]:
	def ident(x: bytes) -> bytes:
		return x

	compressions: dict[str, Compression] = {
		"": Compression(ident, ident),
	}
	for name, loader in _basicCompressionModules.items():
		m: CompressionModule
		try:
			m = loader()
		except ImportError:
			warnings.showwarning(
				message=f"{name} is not available",
				category=ImportWarning,
				filename=__file__,
				lineno=0,
			)
			continue

		def compress_new(x: bytes, m: CompressionModule = m) -> bytes:
			return m.compress(x, 9)

		compressions[name] = Compression(compress_new, m.decompress)

	try:
		import lzma
	except ImportError:
		warnings.warn("lzma is not available", stacklevel=1)
	else:
		filters = [{"id": lzma.FILTER_LZMA2}]
		compressions["lzma2"] = Compression(
			lambda s: lzma.compress(
				s,
				format=lzma.FORMAT_RAW,
				filters=filters,
			),
			lambda s: lzma.decompress(
				s,
				format=lzma.FORMAT_RAW,
				filters=filters,
			),
		)
	return compressions


COMPRESSIONS = _init_compressions()
