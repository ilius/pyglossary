# -*- coding: utf-8 -*-
#
# Copyright © 2023 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# based on https://github.com/abelcheung/types-lxml
# under Apache License, Version 2.0, January 2004
# http://www.apache.org/licenses/

import typing
from typing import (
	AnyStr,
	AsyncContextManager,
	ContextManager,
	Literal,
	Mapping,
	TypeAlias,
)

from lxml.etree import QName, _Element

_TextArg: TypeAlias = "str | bytes | QName"
_TagName: TypeAlias = _TextArg


_OutputMethodArg = Literal[
	"html",
	"text",
	"xml",
	"HTML",
	"TEXT",
	"XML",
]


# Element type can not be a protocol or interface or anything
# it's stupid!
Element = _Element


class IncrementalFileWriter(typing.Protocol):
	def write_declaration(
		self: "typing.Self",
		version: "AnyStr | None" = ...,
		standalone: "bool | None" = ...,
		doctype: "AnyStr | None" = ...,
	) -> None:
		...
	def write_doctype(
		self: "typing.Self",
		doctype: "AnyStr | None",
	) -> None:
		...
	def write(
		self: "typing.Self",
		*args: "AnyStr | Element",
		with_tail: bool = ...,
		pretty_print: bool = ...,
		method: _OutputMethodArg | None = ...,
	) -> None:
		...
	def flush(self: "typing.Self") -> None:
		...
	def method(
		self: "typing.Self",
		method: "_OutputMethodArg | None",
	) -> ContextManager[None]:
		raise NotImplementedError
	def element(
		self: "typing.Self",
		tag: _TagName,
		attrib: "Mapping[str, AnyStr] | None" = ...,
		nsmap: "dict[str | None, AnyStr] | None" = ...,
		method: "_OutputMethodArg | None" = ...,
		**_extra: AnyStr,
	) -> ContextManager[None]:
		raise NotImplementedError

class AsyncIncrementalFileWriter(typing.Protocol):
	async def write_declaration(
		self: "typing.Self",
		version: "AnyStr | None" = ...,
		standalone: "bool | None" = ...,
		doctype: "AnyStr | None" = ...,
	) -> None:
		...
	async def write_doctype(
		self: "typing.Self",
		doctype: "AnyStr | None",
	) -> None:
		...
	async def write(
		self: "typing.Self",
		*args: "AnyStr | Element | None",
		with_tail: bool = ...,
		pretty_print: bool = ...,
		method: "_OutputMethodArg | None" = ...,
	) -> None:
		...
	async def flush(self: "typing.Self") -> None:
		...
	def method(
		self: "typing.Self",
		method: "_OutputMethodArg | None",
	) -> AsyncContextManager[None]:
		raise NotImplementedError
	def element(
		self: "typing.Self",
		tag: _TagName,
		attrib: "Mapping[str, AnyStr] | None" = ...,
		nsmap: "dict[str | None, AnyStr] | None" = ...,
		method: "_OutputMethodArg | None" = ...,
		**_extra: AnyStr,
	) -> AsyncContextManager[None]:
		raise NotImplementedError

class T_htmlfile(  # type: ignore # noqa: PGH003
	IncrementalFileWriter,
	ContextManager[IncrementalFileWriter],
	# AsyncIncrementalFileWriter,
	# AsyncContextManager[AsyncIncrementalFileWriter],
):
	pass

# typing.AsyncContextManager
# is generic version of contextlib.AbstractAsyncContextManager
