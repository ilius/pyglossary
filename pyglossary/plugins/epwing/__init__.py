"""
PyGlossary EPWING format plugin.

Japanese EPWING CD-ROM dictionary catalog and article binaries. Read-only
``Reader`` walks EPWING structure via ``converter`` and emits headwords with HTML
definitions for Yomichan-compatible output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.flags import ALWAYS

from .reader import Reader

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
	"Reader",
	"description",
	"enable",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
]

enable = True
lname = "epwing"
name = "EPWING"
description = "EPWING"
extensions = ()
singleFile = False
kind = "directory"
sortOnWrite = ALWAYS
sortKeyName = "headword"
wiki = "https://en.wikipedia.org/wiki/EPWING"
website = (
	"https://web.archive.org/web/20060430114516/http://www.epwing.or.jp/",
	"EPWING Consortium - 2006",
)
relatedFormats: list[str] = ["Yomichan", "JMDict"]
optionsProp: dict[str, Option] = {}

docTail = """### Supported Dictionaries (Subbooks)

The reader includes specialized extractors for the following EPWING subbook titles:

- `三省堂　スーパー大辞林`
- `大辞泉`
- `明鏡国語辞典`
- `故事ことわざの辞典`
- `研究社　新和英大辞典　第５版`
- `広辞苑第六版`
- `広辞苑　第四版`
- `付属資料`
- `学研国語大辞典`
- `古語辞典`
- `故事ことわざ辞典`
- `学研漢和大字典`
"""
