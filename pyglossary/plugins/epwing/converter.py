# Convert EPWING dictionaries to Yomichan format.
#
# Based on yomichan-import (https://github.com/FooSoft/yomichan-import)
#    under the MIT License
#
# Copyright 2016-2023  Yomichan-Import Authors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Convert EPWING dictionary data to glossary entries.

Based on yomichan-import; walks EPWING catalog and article binaries, decodes
Japanese/EUC text, and maps articles to headwords and HTML definitions suitable
for Yomichan and other targets. Used by the EPWING plugin reader path.
"""

from __future__ import annotations

# mypy: ignore-errors
import json
import logging
import mmap
import os
import re
import zipfile
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Iterator

log = logging.getLogger("pyglossary")

__all__ = ["convert_epwing_to_yomichan"]


class dbTerm:
	"""db Term."""

	def __init__(  # noqa: PLR0913
		self,
		expression: str,
		reading: str = "",
		definition_tags: list[str] | None = None,
		rules: list[str] | None = None,
		score: int = 0,
		glossary: list[Any] | None = None,
		sequence: int = 0,
		term_tags: list[str] | None = None,
	) -> None:
		self.expression = expression
		self.reading = reading
		self.definition_tags = definition_tags or []
		self.rules = rules or []
		self.score = score
		self.glossary = glossary or []
		self.sequence = sequence
		self.term_tags = term_tags or []

	def add_definition_tags(self, *tags: str) -> None:
		for tag in tags:
			if tag not in self.definition_tags:
				self.definition_tags.append(tag)

	def add_term_tags(self, *tags: str) -> None:
		for tag in tags:
			if tag not in self.term_tags:
				self.term_tags.append(tag)

	def add_rules(self, *rules: str) -> None:
		for rule in rules:
			if rule not in self.rules:
				self.rules.append(rule)

	def crush(self) -> list[Any]:
		return [
			self.expression,
			self.reading,
			" ".join(self.definition_tags),
			" ".join(self.rules),
			self.score,
			self.glossary,
			self.sequence,
			" ".join(self.term_tags),
		]


class dbKanji:
	"""db Kanji."""

	def __init__(  # noqa: PLR0913
		self,
		character: str,
		onyomi: list[str] | None = None,
		kunyomi: list[str] | None = None,
		tags: list[str] | None = None,
		meanings: list[str] | None = None,
		stats: dict[str, str] | None = None,
	) -> None:
		self.character = character
		self.onyomi = onyomi or []
		self.kunyomi = kunyomi or []
		self.tags = tags or []
		self.meanings = meanings or []
		self.stats = stats or {}

	def crush(self) -> list[Any]:
		return [
			self.character,
			" ".join(self.onyomi),
			" ".join(self.kunyomi),
			" ".join(self.tags),
			self.meanings,
			self.stats,
		]


class EpwingExtractor:
	"""Epwing Extractor."""

	def extract_terms(self, heading: str, text: str, sequence: int) -> list[dbTerm]:
		raise NotImplementedError

	def extract_kanji(self, heading: str, text: str) -> list[dbKanji]:
		heading = self.translate(heading)
		text = self.translate(text)
		return []

	def get_font_narrow(self) -> dict[int, str]:
		return {}

	def get_font_wide(self) -> dict[int, str]:
		return {}

	def get_revision(self) -> str:
		return "epwing"

	def translate(self, text: str) -> str:
		font_narrow = self.get_font_narrow()
		font_wide = self.get_font_wide()

		def repl(match: re.Pattern) -> str:
			mode = match.group(1)
			code = int(match.group(2))
			font = font_narrow if mode == "n" else font_wide
			return font.get(code, "�")

		text = re.sub(r"{{([nw])_(\d+)}}", repl, text)
		return re.sub(r"\n+", "\n", text)


class KoujienExtractor(EpwingExtractor):
	"""Koujien Extractor."""

	def __init__(self) -> None:
		self.parts_exp = re.compile(
			r"([^（【〖]+)(?:【(.*)】)?(?:〖(.*)〗)?(?:（(.*)）)?"
		)
		self.read_group_exp = re.compile(r"[-‐・]+")
		self.exp_var_exp = re.compile(r"\(([^\)]*)\)")
		self.meta_exp = re.compile(r"（([^）]*)）")
		self.v5_exp = re.compile(r"(動.[四五](［[^］]+］)?)|(動..二)")
		self.v1_exp = re.compile(r"(動..一)")

	def extract_terms(self, heading: str, text: str, sequence: int) -> list[dbTerm]:  # noqa: PLR0912
		heading = self.translate(heading)
		text = self.translate(text)

		match = self.parts_exp.match(heading)
		if not match:
			return []

		expressions = []
		readings = []

		expression = match.group(2)
		if expression:
			expression = self.meta_exp.sub("", expression)
			for split in expression.split("・"):
				split_inc = self.exp_var_exp.sub(r"\1", split)
				expressions.append(split_inc)
				if split != split_inc:
					split_exc = self.exp_var_exp.sub("", split)
					expressions.append(split_exc)

		reading = match.group(1)
		if reading:
			reading = self.read_group_exp.sub("", reading)
			readings.append(reading)

		tags = []
		for line in text.split("\n"):
			m = self.meta_exp.search(line)
			if m:
				tags += m.group(1).split("・")

		terms = []
		if not expressions:
			for r in readings:
				term = dbTerm(expression=r, glossary=[text], sequence=sequence)
				self.export_rules(term, tags)
				terms.append(term)
		else:
			for e in expressions:
				for r in readings:
					term = dbTerm(
						expression=e, reading=r, glossary=[text], sequence=sequence
					)
					self.export_rules(term, tags)
					terms.append(term)
		return terms

	def export_rules(self, term: dbTerm, tags: list[str]) -> None:
		for tag in tags:
			if tag == "形":
				term.add_rules("adj-i")
			elif tag == "動サ変" and (
				term.expression.endswith("する") or term.expression.endswith("為る")
			):
				term.add_rules("vs")
			elif term.expression == "来る":
				term.add_rules("vk")
			elif self.v5_exp.search(tag):
				term.add_rules("v5")
			elif self.v1_exp.search(tag):
				term.add_rules("v1")

	def get_revision(self) -> str:
		return "koujien"

	def get_font_wide(self) -> dict[int, str]:
		return {
			41531: "⟨",
			41532: "⟩",
			42017: "⇿",
			42018: "🈑",
			42023: "🈩",
			42024: "🈔",
			42025: "㊇",
			42026: "3",
			42027: "❷",
			42028: "❶",
			42031: "❸",
			42037: "❹",
			42043: "❺",
			42045: "❻",
			42057: "❼",
			42083: "❽",
			42284: "❾",
			42544: "❿",
			42561: "鉏",
			43611: "⓫",
			43612: "⓬",
			44142: "𑖀",
			44856: "㉑",
			44857: "㉒",
			46374: "〔",
			46375: "〕",
			46390: "①",
			46391: "②",
			46392: "③",
			46393: "④",
			46394: "⑤",
			46395: "⑥",
			46396: "⑦",
			46397: "⑧",
			46398: "⑨",
			46399: "⑩",
			46400: "⑪",
			46401: "⑫",
			46402: "⑬",
			46403: "⑭",
			46404: "⑮",
			46405: "⑯",
			46406: "⑰",
			46407: "⑱",
			46408: "⑲",
			46409: "⑳",
			46677: "⇀",
			46420: "⇨",
			47175: "(季)",
			56383: "㋐",
			56384: "㋑",
			56385: "㋒",
			56386: "㋓",
			56387: "㋔",
			56388: "㋕",
			56389: "㋖",
			56390: "㋗",
			56391: "㋘",
			56392: "㋙",
			56393: "㋚",
			56394: "㋛",
			56395: "㋜",
			56396: "㋝",
			56397: "㋞",
			56398: "▷",
		}


class DaijirinExtractor(KoujienExtractor):
	"""Daijirin Extractor."""

	def get_revision(self) -> str:
		return "daijirin2"

	def get_font_narrow(self) -> dict[int, str]:
		return {
			49441: "á",
			49442: "à",
			49443: "â",
			49444: "ä",
			49445: "ã",
			49446: "ā",
			49447: "é",
			49448: "è",
			49449: "ê",
			49450: "ë",
			49451: "ē",
			49452: "í",
			49453: "î",
			49454: "ï",
			49455: "ñ",
			49456: "ó",
			49457: "ò",
			49458: "ô",
			49459: "ö",
			49460: "ř",
			49461: "ú",
			49462: "ü",
			49463: "~",
			49464: "ç",
			49465: "ˇ",
			49466: "ɡ",
			49467: "ŋ",
			49468: "ʒ",
			49469: "ʃ",
			49470: "ɔ",
			49471: "ð",
			49472: "Á",
			49473: "Í",
			49474: "Ú",
			49475: "É",
			49476: "Ó",
			49477: "À",
			49478: "È",
			49479: "Ò",
			49480: "ì",
			49481: "ù",
			49482: "ý",
			49484: "ɑ",
			49485: "ə",
			49487: "ɛ",
			49488: "θ",
			49489: "ʌ",
			49490: "ɒ",
			49500: "æ",
			50037: "ヰ",
			50038: "ヱ",
		}


class DaijisenExtractor(KoujienExtractor):
	"""Daijisen Extractor."""

	def __init__(self) -> None:
		super().__init__()
		self.parts_exp = re.compile(r"([^【]+)(?:【(.*)】)?")
		self.exp_shapes_exp = re.compile(r"[×△＝‐]+")
		self.exp_multi_exp = re.compile(r"】[^【】]*【")
		self.exp_var_exp = re.compile(r"（([^）]*)）")
		self.read_group_exp = re.compile(r"[-‐・]+")
		self.meta_exp = re.compile(r"［([^］]*)］")

	def extract_terms(self, heading: str, text: str, sequence: int) -> list[dbTerm]:
		heading = self.translate(heading)
		text = self.translate(text)

		match = self.parts_exp.match(heading)
		if not match:
			return []

		expressions = []
		expression_raw = match.group(2)
		if expression_raw:
			expression = self.exp_multi_exp.sub("・", expression_raw)
			expression = self.exp_shapes_exp.sub("", expression)

			for split in expression.split("・"):
				split_inc = self.exp_var_exp.sub(r"\1", split)
				expressions.append(split_inc)
				if split != split_inc:
					split_exc = self.exp_var_exp.sub("", split)
					expressions.append(split_exc)

		reading = match.group(1)
		if reading:
			reading = self.read_group_exp.sub("", reading)
			reading = self.exp_var_exp.sub("", reading)

		tags = []
		for line in text.split("\n"):
			m = self.meta_exp.search(line)
			if m:
				tags += m.group(1).split("・")

		terms = []
		if not expressions:
			term = dbTerm(expression=reading, glossary=[text], sequence=sequence)
			self.export_rules(term, tags)
			terms.append(term)
		else:
			for e in expressions:
				term = dbTerm(
					expression=e, reading=reading, glossary=[text], sequence=sequence
				)
				self.export_rules(term, tags)
				terms.append(term)
		return terms

	def get_revision(self) -> str:
		return "daijisen2"


_EPWING_PAGE_SIZE = 2048
_EPWING_CATALOG_SIZE = 164


def _find_name(path: str, name: str) -> str:
	"""Return a child path, matching its name without case sensitivity."""
	for child in os.listdir(path):
		if child.casefold() == name.casefold():
			return os.path.join(path, child)
	raise FileNotFoundError(f"{name} not found in {path}")


def _decode_catalog_title(data: bytes) -> str:
	data = data.split(b"\0", 1)[0]
	if len(data) % 2:
		data = data[:-1]
	return bytes(byte | 0x80 for byte in data).decode("euc_jp", errors="replace").rstrip()


class EpwingBook:
	"""Epwing Book."""

	def __init__(self, path: str) -> None:
		self.path = path
		self.subbooks = []
		self._load()

	def _load(self) -> None:
		catalogs_path = _find_name(self.path, "CATALOGS")
		with open(catalogs_path, "rb") as file:
			data = file.read()

		if len(data) < 16:
			raise ValueError(f"Invalid EPWING CATALOGS: {catalogs_path}")
		subbook_count = int.from_bytes(data[:2], "big")
		version = int.from_bytes(data[2:4], "big")
		catalog_end = 16 + subbook_count * _EPWING_CATALOG_SIZE
		if not subbook_count or len(data) < catalog_end:
			raise ValueError(f"Invalid EPWING CATALOGS: {catalogs_path}")

		for index in range(subbook_count):
			offset = 16 + index * _EPWING_CATALOG_SIZE
			record = data[offset : offset + _EPWING_CATALOG_SIZE]
			title = _decode_catalog_title(record[2:82])
			directory = record[82:90].decode("ascii", errors="replace").rstrip(" \0")
			index_page = int.from_bytes(record[94:96], "big")
			text_name = "HONMON"
			compression_hint = 0

			if version != 1:
				extra_offset = catalog_end + index * _EPWING_CATALOG_SIZE
				extra = data[extra_offset : extra_offset + _EPWING_CATALOG_SIZE]
				if len(extra) == _EPWING_CATALOG_SIZE and extra[4]:
					text_name = (
						extra[4:12].decode("ascii", errors="replace").rstrip(" \0")
					)
					compression_hint = extra[55]

			subbook_path = _find_name(self.path, directory)
			self.subbooks.append(
				EpwingSubbook(
					subbook_path,
					title,
					index_page,
					text_name,
					compression_hint,
				)
			)


class EpwingSubbook:
	"""Epwing Subbook."""

	def __init__(
		self,
		path: str,
		title: str,
		index_page: int,
		text_name: str,
		compression_hint: int,
	) -> None:
		self.path = path
		self.title = title
		self.index_page = index_page
		self.text_name = text_name
		self.compression_hint = compression_hint

	def entries(self) -> Iterator[dict[str, str]]:
		if self.compression_hint:
			raise NotImplementedError("Compressed EPWING HONMON files are not supported")

		data_path = _find_name(self.path, "DATA")
		honmon_path = _find_name(data_path, self.text_name)
		if os.path.getsize(honmon_path) == 0:
			raise ValueError(f"Empty EPWING text file {honmon_path}")
		with open(honmon_path, "rb") as file:
			with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data:
				seen = set()
				for text_pos, heading_pos in self._entry_positions(data):
					if text_pos in seen:
						continue
					seen.add(text_pos)
					yield {
						"heading": self._read_content(data, heading_pos, heading=True),
						"text": self._read_content(data, text_pos, heading=False),
					}

	def _entry_positions(
		self, data: mmap.mmap
	) -> Iterator[tuple[tuple[int, int], tuple[int, int]]]:
		index_page = self._page(data, self.index_page)
		index_count = index_page[1]
		if index_count >= _EPWING_PAGE_SIZE // 16 - 1:
			raise ValueError(f"Invalid EPWING index table in {self.text_name}")

		word_indexes = {}
		for index in range(index_count):
			offset = 16 + index * 16
			index_id = index_page[offset]
			if index_id in {0x90, 0x91, 0x92}:
				word_indexes[index_id] = int.from_bytes(
					index_page[offset + 2 : offset + 6], "big"
				)

		# Match zero-epwing's alphabet, kana, then as-is search order.
		for index_id in (0x92, 0x90, 0x91):
			if start_page := word_indexes.get(index_id):
				yield from self._leaf_positions(data, start_page)

	def _leaf_positions(  # noqa: PLR0912
		self, data: mmap.mmap, page_number: int
	) -> Iterator[tuple[tuple[int, int], tuple[int, int]]]:
		for _depth in range(16):
			page = self._page(data, page_number)
			page_id = page[0]
			if page_id & 0x80:
				break
			entry_length = page[1]
			entry_count = int.from_bytes(page[2:4], "big")
			if not entry_count:
				raise ValueError(f"Empty EPWING index page {page_number}")
			if entry_length:
				child_offset = 4 + entry_length
			else:
				key_length = page[4]
				child_offset = 5 + key_length
			page_number = int.from_bytes(page[child_offset : child_offset + 4], "big")
		else:
			raise ValueError("EPWING index is too deep")

		while True:
			page = self._page(data, page_number)
			page_id = page[0]
			if not page_id & 0x80:
				raise ValueError(f"Expected EPWING leaf page {page_number}")
			entry_length = page[1]
			entry_count = int.from_bytes(page[2:4], "big")
			offset = 4

			for _index in range(entry_count):
				if page_id & 0x10:
					group_id = page[offset]
					key_length = page[offset + 1]
					if group_id == 0x80:
						offset += key_length + 4
						continue
					if group_id not in {0x00, 0xC0}:
						raise ValueError(f"Invalid EPWING group ID {group_id:#x}")
					position_offset = offset + key_length + 2
					offset += key_length + 14
				elif entry_length:
					position_offset = offset + entry_length
					offset += entry_length + 12
				else:
					key_length = page[offset]
					position_offset = offset + key_length + 1
					offset += key_length + 13

				if offset > _EPWING_PAGE_SIZE:
					raise ValueError(f"Invalid EPWING leaf page {page_number}")
				text_pos = self._position(page, position_offset)
				heading_pos = self._position(page, position_offset + 6)
				yield text_pos, heading_pos

			if page_id & 0x20:
				break
			page_number += 1

	@staticmethod
	def _page(data: mmap.mmap, page_number: int) -> bytes:
		start = (page_number - 1) * _EPWING_PAGE_SIZE
		end = start + _EPWING_PAGE_SIZE
		if page_number < 1 or end > len(data):
			raise ValueError(f"Invalid EPWING page number {page_number}")
		return data[start:end]

	@staticmethod
	def _position(page: bytes, offset: int) -> tuple[int, int]:
		return (
			int.from_bytes(page[offset : offset + 4], "big"),
			int.from_bytes(page[offset + 4 : offset + 6], "big"),
		)

	def _read_content(  # noqa: PLR0912
		self,
		data: mmap.mmap,
		position: tuple[int, int],
		*,
		heading: bool,
	) -> str:
		offset = (position[0] - 1) * _EPWING_PAGE_SIZE + position[1]
		output = bytearray()
		narrow = False
		skip_code = None
		auto_stop_code = None
		printable_count = 0

		while offset < len(data):
			first = data[offset]
			if first == 0x1F:
				if offset + 1 >= len(data):
					break
				code = data[offset + 1]
				if code == 0x03:
					break
				if code == 0x41 and offset + 3 < len(data):
					argument = int.from_bytes(data[offset + 2 : offset + 4], "big")
					if not heading and printable_count and argument == auto_stop_code:
						break
					if auto_stop_code is None:
						auto_stop_code = argument
				if code == 0x0A:
					if heading:
						break
					if skip_code is None:
						output.append(0x0A)
				elif code == 0x04:
					narrow = True
				elif code == 0x05:
					narrow = False

				soft_stop = code == 0x6C or (
					code == 0x4B
					and offset + 9 < len(data)
					and data[offset + 8 : offset + 10] == b"\x1f\x6b"
				)
				step, new_skip = self._control_step(data, offset, code)
				if new_skip is not None:
					skip_code = new_skip
				elif skip_code == code:
					skip_code = None
				offset += step
				if soft_stop:
					break
				continue

			if offset + 1 >= len(data):
				break
			second = data[offset + 1]
			printable_count += 1
			if skip_code is None:
				if 0x20 < first < 0x7F and 0x20 < second < 0x7F:
					ascii_byte = self._narrow_ascii(first, second) if narrow else None
					if ascii_byte is None:
						output.extend((first | 0x80, second | 0x80))
					else:
						output.append(ascii_byte)
				elif 0xA0 < first < 0xFF and 0x20 < second < 0x7F:
					mode = "n" if narrow else "w"
					output.extend(f"{{{{{mode}_{first << 8 | second}}}}}".encode())
				else:
					raise ValueError(f"Invalid EPWING character at offset {offset}")
			offset += 2

		return output.decode("euc_jp", errors="replace")

	@staticmethod
	def _control_step(data: mmap.mmap, offset: int, code: int) -> tuple[int, int | None]:
		steps = {
			0x09: 4,
			0x14: 4,
			0x1A: 4,
			0x1B: 4,
			0x1C: 4,
			0x1D: 4,
			0x1E: 4,
			0x1F: 4,
			0x39: 46,
			0x3C: 20,
			0x41: 4,
			0x44: 12,
			0x45: 4,
			0x4A: 18,
			0x4B: 8,
			0x4C: 4,
			0x4D: 20,
			0x4F: 34,
			0x52: 8,
			0x53: 10,
			0x62: 8,
			0x63: 8,
			0x64: 8,
			0xE0: 4,
		}
		step = steps.get(code, 2)
		if code == 0x42:
			step = 4 if offset + 2 < len(data) and data[offset + 2] == 0 else 2
		elif code == 0x45 and offset + 2 < len(data) and data[offset + 2] == 0x1F:
			step = 2
		elif (
			code == 0x4B
			and offset + 9 < len(data)
			and data[offset + 8 : offset + 10] == b"\x1f\x6b"
		):
			step = 10

		if offset + step > len(data):
			raise ValueError(f"Truncated EPWING control code {code:#x}")
		if code == 0x14:
			return step, 0x15
		if code in {
			0x35,
			0x36,
			0x37,
			0x38,
			0x3A,
			0x3B,
			0x3D,
			0x3E,
			0x3F,
			0x49,
			0x4E,
			*range(0x70, 0x90),
		}:
			return step, code + 0x20
		if code in range(0xE4, 0xFF, 2):
			return step, code + 1
		return step, None

	@staticmethod
	def _narrow_ascii(first: int, second: int) -> int | None:
		if first == 0x23:
			if 0x30 <= second <= 0x39 or 0x41 <= second <= 0x5A:
				return second
			if 0x61 <= second <= 0x7A:
				return second
		if first != 0x21:
			return None
		return {
			0x21: 0x20,
			0x24: 0x2C,
			0x25: 0x2E,
			0x27: 0x3A,
			0x28: 0x3B,
			0x29: 0x3F,
			0x2A: 0x21,
			0x2E: 0x60,
			0x30: 0x5E,
			0x31: 0x7E,
			0x32: 0x5F,
			0x3E: 0x2D,
			0x3F: 0x2F,
			0x40: 0x5C,
			0x43: 0x7C,
			0x47: 0x27,
			0x49: 0x22,
			0x4A: 0x28,
			0x4B: 0x29,
			0x4E: 0x5B,
			0x4F: 0x5D,
			0x50: 0x7B,
			0x51: 0x7D,
			0x5C: 0x2B,
			0x5D: 0x2D,
			0x61: 0x3D,
			0x63: 0x3C,
			0x64: 0x3E,
			0x6F: 0x5C,
			0x70: 0x24,
			0x73: 0x25,
			0x74: 0x23,
			0x75: 0x26,
			0x76: 0x2A,
			0x77: 0x40,
		}.get(second)


class MeikyouExtractor(KoujienExtractor):
	"""Meikyou Extractor."""

	def __init__(self) -> None:
		super().__init__()
		self.parts_exp = re.compile(
			r"([^（【〖\[]+)(?:【(.*)】)?(?:\[(.*)\])?(?:（(.*)）)?"
		)
		self.exp_shapes_exp = re.compile(r"[▼▽]+")
		self.exp_bracketed_exp = re.compile(r"(?:[〈《])([^〉》]*)(?:[〉》])")
		self.exp_terms_exp = re.compile(r"([^（]*)?(?:（(.*)）)?")
		self.read_group_exp = re.compile(r"[-‐・]+")
		self.meta_exp = re.compile(r"〘([^〙]*)〙")

	def extract_terms(  # noqa: PLR0912
		self,
		heading: str,
		text: str,
		sequence: int,
	) -> list[dbTerm]:
		heading = self.translate(heading)
		text = self.translate(text)

		match = self.parts_exp.match(heading)
		if not match:
			return []

		expressions = []
		readings = []

		# Expression from 【...】
		exp_match = match.group(2)
		if exp_match:
			exp_match = self.exp_shapes_exp.sub("", exp_match)
			exp_match = self.exp_bracketed_exp.sub(r"\1", exp_match)
			terms_match = self.exp_terms_exp.match(exp_match)
			if terms_match:
				for group in terms_match.groups():
					if group:
						expressions += group.split("・")

		# Expression from [...] (foreign/meta)
		foreign_match = match.group(3)
		if foreign_match:
			# Simplified foreign meta removal (Go version has a long list, we just split)
			foreign_match = foreign_match.replace("＋", " ")
			expressions += foreign_match.split("・")

		reading = match.group(1)
		if reading:
			reading = self.read_group_exp.sub("", reading)
			readings.append(reading)

		tags = []
		for line in text.split("\n"):
			m = self.meta_exp.search(line)
			if m:
				tags += m.group(1).split("・")

		terms = []
		if not expressions:
			for r in readings:
				term = dbTerm(expression=r, glossary=[text], sequence=sequence)
				self.export_rules(term, tags)
				terms.append(term)
		else:
			for e in expressions:
				for r in readings:
					term = dbTerm(
						expression=e, reading=r, glossary=[text], sequence=sequence
					)
					self.export_rules(term, tags)
					terms.append(term)
		return terms

	def get_revision(self) -> str:
		return "meikyou1"

	def get_font_narrow(self) -> dict[int, str]:
		# Basic mapping for Meikyou
		return {41550: "ī"}


class GakkenExtractor(KoujienExtractor):
	"""Gakken Extractor."""

	def __init__(self) -> None:
		super().__init__()
		self.parts_exp = re.compile(r"([ぁ-んァ-ヶー‐・]*)(?:【(.*)】)?")
		self.read_group_exp = re.compile(r"[-‐・]+")
		# Ported from gakken.go cosmetics replacer
		self.cosmetics = {
			"(1)": "①",
			"(2)": "②",
			"(3)": "③",
			"(4)": "④",
			"(5)": "⑤",
			"カ゛": "ガ",
			"キ゛": "ギ",
			"ク゛": "グ",
			"ケ゛": "ゲ",
			"コ゛": "ゴ",
			"タ゛": "ダ",
			"チ゛": "ヂ",
			"ツ゛": "ヅ",
			"テ゛": "デ",
			"ト゛": "ド",
			"ハ゛": "バ",
			"ヒ゛": "ビ",
			"フ゛": "ブ",
			"ヘ゛": "ベ",
			"ホ゛": "ボ",
			"サ゛": "ザ",
			"シ゛": "ジ",
			"ス゛": "ズ",
			"セ゛": "ゼ",
			"ソ゛": "ゾ",
		}

	def _apply_cosmetics(self, text: str) -> str:
		for k, v in self.cosmetics.items():
			text = text.replace(k, v)
		return text

	def extract_terms(  # noqa: PLR0912
		self,
		heading: str,
		text: str,
		sequence: int,
	) -> list[dbTerm]:
		heading = self.translate(heading)
		text = self.translate(text)
		text = self._apply_cosmetics(text)

		match = self.parts_exp.match(heading)
		if not match:
			return []

		expressions = []
		readings = []

		expression_raw = match.group(2)
		if expression_raw:
			expression = self.meta_exp.sub("", expression_raw)
			for split in re.split(r"・|】【", expression):
				split_inc = self.exp_var_exp.sub(r"\1", split)
				expressions.append(split_inc)
				if split != split_inc:
					split_exc = self.exp_var_exp.sub("", split)
					expressions.append(split_exc)

		reading = match.group(1)
		if reading:
			reading = self.read_group_exp.sub("", reading)
			readings.append(reading)

		tags = []
		for line in text.split("\n"):
			m = self.meta_exp.search(line)
			if m:
				tags.append(m.group(1).split("・"))

		if not readings:
			readings = [""]

		terms = []
		if not expressions:
			for r in readings:
				if not r:
					continue
				term = dbTerm(expression=r, glossary=[text], sequence=sequence)
				self.export_rules(term, tags)
				terms.append(term)
		else:
			for e in expressions:
				for r in readings:
					term = dbTerm(
						expression=e, reading=r, glossary=[text], sequence=sequence
					)
					self.export_rules(term, tags)
					terms.append(term)
		return terms

	def get_revision(self) -> str:
		return "gakken"


class WadaiExtractor(KoujienExtractor):
	"""Wadai Extractor."""

	def __init__(self) -> None:
		super().__init__()
		self.parts_exp = re.compile(r"([^＜]+)(?:＜([^＞【]+)(?:【([^】]+)】)?＞)?")
		self.literal_parts_exp = re.compile(r"(¶)?(.*)")
		self.read_parts_exp = re.compile(r"([^１２３４５６７８９０]+)(.*)")
		self.quoted_exp = re.compile(r"「?([^」]+)")
		self.alpha_exp = re.compile(r"[a-z]+")

	def extract_terms(self, heading: str, text: str, sequence: int) -> list[dbTerm]:
		heading = self.translate(heading)
		text = self.translate(text)

		match = self.parts_exp.match(heading)
		if not match:
			return []

		preset = False
		literal = match.group(1)
		lit_match = self.literal_parts_exp.match(literal)
		if lit_match:
			preset = bool(lit_match.group(1))
			literal = lit_match.group(2)

		reading = match.group(2) or ""
		read_match = self.read_parts_exp.match(reading)
		if read_match:
			reading = read_match.group(1)

		expressions = (match.group(3) or "").split("・")
		if not expressions or expressions == [""]:
			expressions = [""]

		terms = []
		for expression_ in expressions:
			expression = expression_
			if preset:
				expression = literal
				reading = ""
			elif not expression:
				expression = literal

			quoted_match = self.quoted_exp.match(reading)
			if quoted_match:
				reading = quoted_match.group(1)

			if self.alpha_exp.match(expression) and reading:
				expression = reading
				reading = ""

			expression = expression.strip()
			if not expression:
				continue

			term = dbTerm(
				expression=expression, reading=reading, glossary=[text], sequence=sequence
			)
			terms.append(term)
		return terms

	def get_revision(self) -> str:
		return "wadai1"


class KotowazaExtractor(EpwingExtractor):
	"""Kotowaza Extractor."""

	def __init__(self) -> None:
		self.read_group_exp = re.compile(r"([^ぁ-ゖァ-ヺ]*)(\([^)]*\))")
		self.read_group_alts_exp = re.compile(r"\(([^)]*)\)")
		self.read_group_no_alts_exp = re.compile(r"\(([^・)]*)\)")
		self.word_group_exp = re.compile(r"＝([^〔＝]*)〔＝([^〕]*)〕")

	def extract_terms(self, heading: str, text: str, sequence: int) -> list[dbTerm]:
		heading = self.translate(heading)
		text = self.translate(text)

		queue = [heading]
		reduced_expressions = []

		while queue:
			expression = queue.pop(0)
			match = self.word_group_exp.search(expression)
			if not match:
				reduced_expressions.append(expression)
			else:
				replacements = [match.group(1)]
				replacements += match.group(2).split("・")
				for repl in replacements:
					queue.append(expression.replace(match.group(0), repl))  # noqa: PERF401

		terms = []
		for red_exp in reduced_expressions:
			expression = self.read_group_exp.sub(r"\1", red_exp)
			read_alts_exp = self.read_group_exp.sub(r"\2", red_exp)
			read_alts_exp = self.read_group_no_alts_exp.sub(r"\1", read_alts_exp)

			readings = []
			read_queue = [read_alts_exp]
			while read_queue:
				read_item = read_queue.pop(0)
				match = self.read_group_alts_exp.search(read_item)
				if not match:
					readings.append(read_item)
				else:
					for repl in match.group(1).split("・"):
						read_queue.append(read_item.replace(match.group(0), repl))  # noqa: PERF401

			for r in readings:
				term = dbTerm(
					expression=expression, reading=r, glossary=[text], sequence=sequence
				)
				terms.append(term)
		return terms

	def get_revision(self) -> str:
		return "kotowaza1"


def convert_epwing_to_yomichan(
	input_path: str,
	output_path: str,
	title: str = "",
	stride: int = 10000,
	pretty: bool = False,
) -> None:
	log.info(f"EPWING: Converting {input_path}...")
	book = EpwingBook(input_path)

	extractors_map = {
		"三省堂　スーパー大辞林": DaijirinExtractor(),
		"大辞泉": DaijisenExtractor(),
		"明鏡国語辞典": MeikyouExtractor(),
		"故事ことわざの辞典": KotowazaExtractor(),
		"研究社　新和英大辞典　第５版": WadaiExtractor(),
		"広辞苑第六版": KoujienExtractor(),
		"広辞苑　第四版": KoujienExtractor(),
		"付属資料": KoujienExtractor(),
		"学研国語大辞典": GakkenExtractor(),
		"古語辞典": GakkenExtractor(),
		"故事ことわざ辞典": GakkenExtractor(),
		"学研漢和大字典": GakkenExtractor(),
	}

	all_terms = []
	all_kanji = []
	revisions = []
	titles = []
	sequence = 0

	for subbook in book.subbooks:
		extractor = extractors_map.get(subbook.title)
		if not extractor:
			log.warning(f"EPWING: Skipping unknown subbook '{subbook.title}'")
			continue

		log.info(f"EPWING: Processing subbook '{subbook.title}'")

		for entry in subbook.entries():
			# Translate font markers in entry["heading"] and entry["text"]

			terms = extractor.extract_terms(entry["heading"], entry["text"], sequence)
			all_terms += terms
			all_kanji += extractor.extract_kanji(entry["heading"], entry["text"])
			sequence += 1

		revisions.append(extractor.get_revision())
		titles.append(subbook.title)

	if not title:
		title = ", ".join(titles)

	log.info(f"EPWING: Writing {len(all_terms)} terms to {output_path}")

	with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
		index = {
			"title": title,
			"revision": ";".join(revisions),
			"sequenced": True,
			"format": 3,
			"author": "pyglossary-epwing-pure",
			"url": "https://github.com/FooSoft/yomichan-import",
		}
		z.writestr(
			"index.json",
			json.dumps(index, indent=4 if pretty else None, ensure_ascii=False),
		)

		for i in range(0, len(all_terms), stride):
			batch = all_terms[i : i + stride]
			bank_num = (i // stride) + 1
			content = [t.crush() for t in batch]
			z.writestr(
				f"term_bank_{bank_num}.json",
				json.dumps(content, indent=4 if pretty else None, ensure_ascii=False),
			)

		for i in range(0, len(all_kanji), stride):
			batch = all_kanji[i : i + stride]
			bank_num = (i // stride) + 1
			content = [k.crush() for k in batch]
			z.writestr(
				f"kanji_bank_{bank_num}.json",
				json.dumps(content, indent=4 if pretty else None, ensure_ascii=False),
			)

	log.info("EPWING: Conversion successful.")
