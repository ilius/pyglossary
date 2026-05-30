# -*- coding: utf-8 -*-
"""Incremental Markdown emitter matching freedict.Reader htmlfile usage."""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
	from collections.abc import Iterator

__all__ = ["MdEmit"]

_LIST_LINE_RE = re.compile(r"^\t*(?:\d+\.|-\s)")


def _md_url(url: str) -> str:
	return quote(url, safe="/:?#[]@!$&'()*+,;=%._~-")


class MdEmit:
	"""Tiny htmlfile-compatible surface: ``.write()`` and ``.element()``."""

	__slots__ = ("_bufs", "_list_levels", "_parts")

	def __init__(self) -> None:
		self._parts: list[str] = []
		self._bufs: list[list[str]] | None = None
		self._list_levels: list[dict[str, Any]] = []

	def _effective_append(self, s: str) -> None:
		if self._bufs is None:
			self._parts.append(s)
		else:
			self._bufs[-1].append(s)

	def write(self, chunk: Any) -> None:
		from lxml import etree as ET

		if ET.iselement(chunk):
			tag_val = getattr(chunk, "tag", "")
			tag_l = (
				tag_val.lower()
				if isinstance(tag_val, str)
				else str(tag_val).lower().split("}")[-1]
			)
			if tag_l == "br":
				self._effective_append("\n")
			return
		txt = chunk if isinstance(chunk, str) else str(chunk)
		self._effective_append(txt.replace("\xa0", " "))

	def finish(self) -> str:
		s = "".join(self._parts)
		s = re.sub(r"[ \t]+\n", "\n", s)
		s = re.sub(r"\n{3,}", "\n\n", s)
		return s.strip()

	@contextmanager
	def element(
		self,
		tag: str,
		attrib: dict[str, Any] | None = None,
		**kwargs: Any,
	) -> Iterator[None]:
		attr = dict(attrib or ())
		attr.update(kwargs)
		t = tag.lower()
		handler = getattr(self, f"_ctx_{t}", self._ctx_pass)
		with handler(attr):
			yield

	@contextmanager
	@staticmethod
	def _ctx_pass(_attr: dict[str, Any]) -> Iterator[None]:
		yield

	@contextmanager
	def _ctx_div(self, attr: dict[str, Any]) -> Iterator[None]:
		cls = attr.get("class", "")
		classes = cls.split() if cls else []

		if "example" in classes:
			self._bufs = self._bufs or []
			self._bufs.append([])
			try:
				yield
			finally:
				buf_list = self._bufs.pop()
				body = "" if not buf_list else "".join(buf_list).strip()
				if not self._bufs:
					self._bufs = None
				if body:
					if self._parts and not self._parts[-1].endswith("\n"):
						self._effective_append("\n")
					for ln in body.splitlines() or [" "]:
						ln_strip = ln.strip()
						line = "> " + (ln_strip or "")
						self._effective_append(line + "\n")
			return

		if attr.get("dir") == "rtl":
			self._effective_append("\n")
			try:
				yield
			finally:
				self._effective_append("\n")
			return

		yield

	@contextmanager
	def _ctx_font(self, attr: dict[str, Any]) -> Iterator[None]:
		cls = attr.get("class", "") or ""
		grammar = "grammar" in cls.split()
		if grammar:
			self._effective_append("*")
			yield  # noqa: RUF075
			self._effective_append("*")
			return
		yield

	@contextmanager
	def _ctx_b(self, attr: dict[str, Any]) -> Iterator[None]:
		del attr
		self._effective_append("**")
		yield  # noqa: RUF075
		self._effective_append("**")

	@contextmanager
	def _ctx_strong(self, attr: dict[str, Any]) -> Iterator[None]:
		del attr
		self._effective_append("**")
		yield  # noqa: RUF075
		self._effective_append("**")

	@contextmanager
	def _ctx_big(self, attr: dict[str, Any]) -> Iterator[None]:
		del attr
		self._effective_append("## ")
		yield  # noqa: RUF075
		self._effective_append("\n")

	@contextmanager
	@staticmethod
	def _ctx_span(attr: dict[str, Any]) -> Iterator[None]:
		del attr
		yield

	@contextmanager
	def _ctx_p(self, attr: dict[str, Any]) -> Iterator[None]:
		del attr
		self._effective_append("\n\n")
		yield  # noqa: RUF075
		self._effective_append("\n\n")

	@contextmanager
	def _ctx_a(self, attr: dict[str, Any]) -> Iterator[None]:
		self._bufs = self._bufs or []
		self._bufs.append([])
		href = (attr.get("href") or "").strip()
		try:
			yield
		finally:
			buf_list = self._bufs.pop()
			if not self._bufs:
				self._bufs = None
			label = "".join(buf_list).replace("\xa0", " ").strip()
			link = label if not href else f"[{label}]({_md_url(href)})"
			self._effective_append(link)

	@contextmanager
	def _ctx_ol(self, attr: dict[str, Any]) -> Iterator[None]:
		del attr
		self._list_levels.append({"ordered": True, "next": 1})
		if self._parts and self._parts[-1] not in {"\n", "\n\n"}:
			self._effective_append("\n")
		yield  # noqa: RUF075
		self._list_levels.pop()
		self._effective_append("\n")

	@contextmanager
	def _ctx_ul(self, attr: dict[str, Any]) -> Iterator[None]:
		del attr
		self._list_levels.append({"ordered": False, "next": 0})
		if self._parts and self._parts[-1] not in {"\n", "\n\n"}:
			self._effective_append("\n")
		yield  # noqa: RUF075
		self._list_levels.pop()
		self._effective_append("\n")

	@contextmanager
	def _ctx_li(self, attr: dict[str, Any]) -> Iterator[None]:  # noqa: PLR0912
		del attr
		level = len(self._list_levels)
		if not level:
			yield
			return

		meta = self._list_levels[-1]
		start = len(self._parts)

		yield  # noqa: RUF075

		raw = "".join(self._parts[start:])
		del self._parts[start:]
		block = raw.strip("\n")

		tabs = "\t" * max(0, level - 1)
		if meta["ordered"]:
			n = meta["next"]
			meta["next"] = n + 1
			head = f"{tabs}{n}. "
		else:
			head = f"{tabs}- "

		if not block:
			self._effective_append(head + "\n")
			return

		lines = block.split("\n")
		split_at = len(lines)
		for i, ln in enumerate(lines):
			if _LIST_LINE_RE.match(ln):
				split_at = i
				break

		plain = lines[:split_at]
		nested = lines[split_at:]
		cont_tab = tabs + "\t"

		if plain:
			self._effective_append(head + plain[0] + "\n")
			for ln in plain[1:]:
				if _LIST_LINE_RE.match(ln):
					self._effective_append(ln + "\n")
				else:
					self._effective_append(cont_tab + ln + "\n")
		else:
			self._effective_append(head + "\n")

		for ln in nested:
			if _LIST_LINE_RE.match(ln):
				self._effective_append(ln + "\n")
			else:
				self._effective_append(cont_tab + ln + "\n")
