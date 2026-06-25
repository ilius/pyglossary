from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import EncodingOption, StrOption

from .reader import Reader

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
	"Reader",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "wordfrequency"
name = "WordFrequency"
description = "WordFrequency.info COCA lemma list (.wordfrequency)"
extensions = (".wordfrequency",)
extensionCreate = ".wordfrequency"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://www.wordfrequency.info/",
	"Word frequency data (COCA)",
)

optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"gram_color": StrOption(
		comment="Grammar color",
	),
}

docTail = """\
### Input format

Tab-separated lemma frequency lists from [WordFrequency.info](https://www.wordfrequency.info/)
(COCA corpus), e.g. `lemmas_60k.txt`.
"""


# Some words have multiple PoS rows:	PoS rows
# blue: noun (n), verb (v)
# board: verb (v), preposition (i)
# design: noun (n), verb (v)
# hammer: noun (n), verb (v)
# light: verb (v), preposition (i)
