# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Literal, NotRequired, Required, TypeAlias, Union

from typing_extensions import TypedDict

DefinitionObj: TypeAlias = Union[
	"DefinitionString",
	"DefinitionImage",
	"DefinitionStructContent",
]
YomichanDefinition: TypeAlias = str | DefinitionObj | tuple[str, list[str]]


class DefinitionString(TypedDict):
	type: Literal["text"]
	text: str


class DefinitionImage(TypedDict, total=False):
	type: Required[Literal["image"]]
	path: Required[str]
	width: int
	height: int
	title: str
	alt: str
	description: str
	pixelated: bool
	imageRendering: Literal["auto", "pixelated", "crisp=edges"]
	appearance: Literal["auto", "monochrome"]
	background: bool
	collapsed: bool
	collapsible: bool


class DefinitionStructContent(TypedDict):
	type: Literal["structured-content"]
	content: StructuredContent


StructuredContent: TypeAlias = Union[
	str,
	list["StructuredContent"],
	"StructuredContentObj",
]

StructuredContentObj: TypeAlias = Union[
	"EmptyTagStructContent",
	"GenericContainerStructContent",
	"TableStructContent",
	"StylishContainerStructContent",
	"ImageTagStructContent",
	"LinkTagStructContent",
]
DataAttributes: TypeAlias = dict[str, str]
StyleAttributes: TypeAlias = dict[str, str | int]


class EmptyTagStructContent(TypedDict):
	tag: Literal["br"]
	data: NotRequired[DataAttributes]


class GenericContainerStructContent(TypedDict, total=False):
	tag: Required[Literal["ruby", "rt", "rp", "table", "thead", "tbody", "tfoot", "tr"]]
	content: StructuredContent
	data: DataAttributes
	lang: str


class TableStructContent(TypedDict, total=False):
	tag: Required[Literal["td", "th"]]
	content: StructuredContent
	data: DataAttributes
	colSpan: int
	rowSpan: int
	style: StyleAttributes
	lang: str


class StylishContainerStructContent(TypedDict, total=False):
	tag: Required[Literal["span", "div", "ol", "ul", "li", "details", "summary"]]
	content: StructuredContent
	data: DataAttributes
	style: StyleAttributes
	# Hover text
	title: str
	open: bool
	lang: str


class ImageTagStructContent(TypedDict, total=False):
	tag: Required[Literal["img"]]
	data: DataAttributes
	path: Required[str]
	width: float
	height: float
	# Hover text
	title: str
	alt: str
	description: str
	pixelated: bool
	imageRendering: Literal["auto", "pixelated", "crisp=edges"]
	appearance: Literal["auto", "monochrome"]
	background: bool
	collapsed: bool
	collapsible: bool
	verticalAlign: Literal[
		"baseline", "sub", "super", "text-top", "text-bottom", "middle", "top", "bottom"
	]  # noqa: E501
	border: str
	borderRadius: str
	# The units for the width and height
	sizeUnits: Literal["px", "em"]


class LinkTagStructContent(TypedDict, total=False):
	tag: Required[Literal["a"]]
	content: StructuredContent
	href: Required[str]
	lang: str
