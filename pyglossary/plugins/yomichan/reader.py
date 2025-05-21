# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import (
    TYPE_CHECKING,
    TypedDict,
)
from zipfile import ZipFile

from pyglossary.json_utils import jsonToData

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator
    from typing import Literal, TypeAlias

    from typing_extensions import Required

    from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]

FIELDS_TO_WRITE = ["title", "author", "description", "sourceLanguage", "targetLanguage"]
TERM_BASE_PATTERN = re.compile(r"term_bank_(\d+).json\Z")


class Reader:
    useByteProgress = False
    compressions = ["zip"]

    def __init__(self, glos: ReaderGlossaryType) -> None:
        self._glos = glos
        self.clear()

    def clear(self) -> None:
        self._dictFile: ZipFile | None = None
        self._filename = ""
        self._isSequenced = False
        self._termFiles = []

    def open(self, filename: str) -> None:
        # TODO: Sanitize name
        self._filename = filename
        self._dictFile = ZipFile(filename)
        termFiles: list[tuple[int, str]] = []
        for file in self._dictFile.filelist:
            match = TERM_BASE_PATTERN.match(file.filename)
            if match is None:
                continue
            termFiles.append((int(match.group(1)), file.filename))
        self._termFiles = [val for _, val in sorted(termFiles, key=lambda v: v[0])]
        self._ReadIndex()

    def close(self) -> None:
        if self._dictFile:
            self._dictFile.close()
        self.clear()

    def __len__(self) -> int:
        # TODO: LEN
        return 0


    def __iter__(self) -> Iterator[EntryType]:
        for termFile in self._termFiles:
            yield from self._ReadTermBank(termFile)
        yield from self._ReadUsedResources()


    def _ReadIndex(self) -> None:
        with self._dictFile.open("index.json") as indexFile:
            index = jsonToData(indexFile.read())
        assert isinstance(index, dict), "Invalid format"
        if index["format"] != 3:
            raise NotImplementedError("Supported only dictionaries of 3 version")
        self._glos.setInfo("sourceLang", "ja")
        for c_field in FIELDS_TO_WRITE:
            value = index.get(c_field)
            if value is not None:
                self._glos.setInfo(c_field, value)
        self._isSequenced = index.get("isSequenced", False)

    def _ReadTermBank(self, termBankName: str) -> Generator[EntryType, None, None]:
        with self._dictFile.open(termBankName) as termBankFile:
            termBank = jsonToData(termBankFile.read())
        for term in termBank:
            word = term[0]
            if (reading := term[1]):
                word = [word, reading]
            definition = _ReadDefinition(term[5])
            yield self._glos.newEntry(word, definition, defiFormat="h")

    def _ReadUsedResources(self) -> Generator[EntryType, None, None]:
        for file in self._dictFile.filelist:
            if file.is_dir() or \
                file.filename in self._termFiles or \
                file.filename == "index.json":
                continue
            with self._dictFile.open(file.filename) as rawFile:
                data = rawFile.read()
            yield self._glos.newDataEntry(file.filename, data)


class StructuredContent(TypedDict, total=False):
    type: Required[Literal["text", "structured-content", "img"]]
    # Text
    text: str
    # Structured Content
    content: StructuredContentChild
    # Image
    path: str
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


class StructuredContentChildObj(TypedDict, total=False):
    tag: Required[Literal["br", "div", "img", "a"]]
    content: "StructuredContentChildObj"
    data: dict[str, str]
    # Local image file
    path: str
    # Only for links will be match for r"^(?:https?:|\?)[\w\W]*"
    #   Internal links start from ?
    href: str
    lang: str


if TYPE_CHECKING:
    StructuredContentChild: TypeAlias = str | list["StructuredContentChild"] | "StructuredContentChildObj"
    YomichanDefinitionType = str | StructuredContent | list


def _ReadSubStructuredContent(elem: StructuredContentChild) -> str:
    if isinstance(elem, str):
        return elem
    if isinstance(elem, list):
        return " ".join(map(_ReadSubStructuredContent, elem))
    additional_properties = "".join((
        f' {key}="{val}"'
        for key, val in elem.get("data", {}).items()
    ))
    # TODO: Process all tags?
    if elem["tag"] == "a":
        additional_properties += f' href="{elem["href"]}"'
    if elem["tag"] == "img":
        tag = f"<img src=\"{elem['path']}\"{additional_properties}>"
    elif elem["tag"] == "br":
        tag = f"<br{additional_properties}>"
    else:
        tag = elem["tag"]
        content = _ReadSubStructuredContent(elem.get("content", ""))
        tag = f"<{tag}{additional_properties}>{content}</{tag}>"
    return tag


def _ReadStructuredContent(elem: StructuredContent) -> str:
    elem_type = elem["type"]
    if elem_type == "text":
        return elem["text"]
    if elem_type == "structured-content":
        return _ReadSubStructuredContent(elem["content"])
    if elem_type == "img":
        return f"<img src=\"{elem['href']}\">"
    raise RuntimeError("Ill-formed Yomichan dictionary")


def _ReadDefinition(definition: list[YomichanDefinitionType]) -> str:
    def _ParseDefinition(defi: YomichanDefinitionType) -> str:
        if isinstance(defi, str):
            return defi
        if isinstance(defi, dict):
            return _ReadStructuredContent(defi)
        raise NotImplementedError("Unknown elem in definition: {defi}")

    return "\n".join(map(_ParseDefinition, definition))


# + Read zip file
# - Read metadata from index.json
# - Read definitions from term base
# - transfer other data required by terms

