# StarDict `k` type (KingSoft PowerWord XML) — investigation

Status: **not implemented**. This note records what would be involved if the
StarDict reader ever gains support for type identifier `k`.

## What the format is

StarDict type `k` is listed in the format spec as "KingSoft PowerWord's data.
The data is a utf-8 string ending with `'\0'`. It is in XML format."

In practice the payload is a PowerWord XML fragment, usually one root element
(`<CK>` for PowerWord 2012, `<单词块>` for older PowerWord releases) whose
child elements contain CDATA sections. It is not a general-purpose XML
document: most human-readable text lives inside CDATA, and the text inside
CDATA contains a custom inline markup language that is not XML.

The reference implementation is StarDict's
`stardict-powerword-parsedata-plugin`:

- <https://github.com/huzheng001/stardict-3/blob/master/dict/stardict-plugins/stardict-powerword-parsedata-plugin/stardict_powerword_parsedata.cpp>

The dictionaries are produced by StarDict's `kingsoft`, `kingsoft2` and
`powerword` tools, which always write `sametypesequence=k`:

- <https://github.com/huzheng001/stardict-3/blob/master/tools/src/kingsoft.cpp>
- <https://github.com/huzheng001/stardict-3/blob/master/tools/src/kingsoft2.cpp>
- <https://github.com/huzheng001/stardict-3/blob/master/tools/src/powerword.cpp>

## Payload shape

A synthetic minimal example (illustrative; not copied from a real dictionary):

```xml
<CK>
	<DC><![CDATA[example]]></DC>
	<CB><![CDATA[ig5zAmpl]]></CB>
	<DX><![CDATA[&{I}n.&{}]]></DX>
	<JX><![CDATA[&{b}example&{} definition]]></JX>
</CK>
```

Notes:

- `k` is a lower-case type identifier, so in the `.dict` file it is terminated
  by `'\0'`. With `sametypesequence=k` the type byte and terminator are
  omitted; the whole definition block is the XML fragment.
- Element names exist in two generations:
  - Chinese element names used by older PowerWord data (`单词块`, `单词`,
    `词典音标`, `单词词性`, `例句原型`, `例句解释`, …).
  - Short Latin names used by PowerWord 2012 (`CK`, `DC`, `CB`, `DX`, `JX`,
    `GZ`, `PY`, `LY`, `LS`, …).
- Text is normally wrapped in CDATA. The StarDict plugin ignores ordinary XML
  text nodes (`parser.text = NULL`), so anything outside CDATA is dropped.

### CDATA quirks

The plugin accepts two CDATA spellings:

- `<![CDATA[ ... ]]>` (normal)
- `[CDATA[ ... ]]` (missing angle brackets), used by some older data

Leading and trailing ASCII whitespace inside the CDATA is stripped. A strict
XML parser such as `xml.etree.ElementTree` cannot be used directly on these
fragments; either normalise the CDATA markers first, or parse only the
`<![CDATA[...]]>` payloads with a small custom scanner.

### Elements with special rendering

The StarDict plugin handles these elements specially:

| Element (old / 2012) | Meaning | StarDict rendering |
| --- | --- | --- |
| `词典音标` / `CB` | phonetic | `[<span foreground="blue">…</span>]` after IPA conversion |
| `单词原型` / `YX` | headword variant | bold, only when different from the current headword |
| `单词词性` / `DX` | part of speech | italic, with inline markup applied |
| `汉语拼音` / `PY` | pinyin | blue, single underline |
| `例句原型` / `LY` | example source | colour `#008080` |
| `例句解释` / `LS` | example translation | colour `#01259A` |

Start tags that emit section headers: `基本词义`, `继承用法`, `习惯用语`,
`词性变化`, `特殊用法`, `参考词汇`, `常用词组`, `语源`, `派生`, `用法`,
`注释`. Their headers are produced as a blue `<…>` span.

All other elements fall through to the generic inline-markup renderer.

## Inline markup inside CDATA

PowerWord text uses an `&{…}` mini-language. The plugin emits Pango markup
(`<b>`, `<i>`, `<span foreground=…>`, …) and escapes normal text.

| Markup | Meaning | Output |
| --- | --- | --- |
| `&{b}` or `&{B}` | bold | `<b>` |
| `&{I}` | italic | `<i>` |
| `&{+}` | superscript | `<sup>` |
| `&{-}` | subscript | `<sub>` |
| `&{x}` | emphasised text | blue, single underline |
| `&{X…}` | phonetic | IPA conversion below, blue |
| `&{2…}` | alternate phonetic | second IPA conversion below, blue |
| `&{l}`, `&{D}` | link | blue, single underline |
| `&{L}`, `&{U}` | link | teal (`#008080`), single underline |
| `&{}` or `}` | close current tag | matching closing tag |
| `<`, `>`, `'`, `"`, `&` | literal text | escaped to entities |

Links are rendered as `query://<text>` in StarDict. A PyGlossary port would
need to decide whether to keep them as text, map them to `<a>` tags, or reuse
PyGlossary's internal link scheme.

If tags are still open at the end of a CDATA block, the plugin closes them in
reverse order.

## Phonetic conversion

Phonetic CDATA (`CB` / `词典音标`, `&{X…}`) uses ASCII characters that must be
translated to IPA. The StarDict plugin has two hard-coded tables.

First table (used by `CB` and `&{X…}`):

| Input | Output | Input | Output |
| --- | --- | --- | --- |
| `A` | `æ` | `B` | `ɑ` |
| `C` | `ɔ` | `D` | `ã` |
| `E` | `ә` | `F` | `ʃ` |
| `G` | `ɣ` | `H` | `Ч` |
| `I` | `i` | `J` | `ʊ` |
| `K` | `ʏ` | `L` | `ɚ` |
| `M` | `ɲ` | `N` | `ŋ` |
| `P` | `ɵ` | `Q` | `ʌ` |
| `R` | `ɔ` | `T` | `ð` |
| `V` | `ʒ` | `W` | `θ` |
| `X` | `Ø` | `Z` | `є` |
| `5` | `'` | `6` | `!` |
| `7` | `͵` | `9` | `ˏ` |
| `_` | `ˇ` | `=` | `ê` |
| `^` | `ɡ` | `\` | `ɜ` |
| `?` | `U` | `@` | `S` |
| `[` | `ə` | | |

Second table (used by `&{2…}` for data such as the PowerWord 2007 edition of
《美国传统词典[双解]》):

| Input | Output | Input | Output |
| --- | --- | --- | --- |
| `8` | `:` | `0` | `Ŋ` |
| `¾` | `ǔ` | `%` | `ɔ` |
| `µ` | `ě` | `³` | `ā` |
| `!` | `I` | `W` | `ɛ` |
| `&` | `U` | `…` | `ə` |
| `¹` | `ǐ` | `“` | `′` |
| `*` | `ə` | `6` | `ˋ` |
| `+` | `ɚ` | `”` | `´` |
| `‘` | `KH` | `$` | `ɑ` |
| `7` | `͵` | `'` | `KH` |
| `½` | `ō` | `¼` | `ǒ` |
| `¶` | `ē` | `º` | `ī` |
| `G` | `θ` | `9` | `ʒ` |
| `.` | `ʃ` | `/` | `ʒ` |
| `²` | `ǎ` | `#` | `æ` |
| `’` | `N` | `Y` | `t` |
| `H` | `ð` | `÷` | `ń` |
| `é` | `ê` | `¿` | `ū` |
| `)` | `ɜ` | `Ó` | `ǒ` |
| `ï` | `Ś` | `Ä` | `ǐ` |
| `\` | `ł` | `›` | `ōō` |
| `‹` | `ǒǒ` | `ý` | `V` |

Characters not in the tables pass through unchanged.

Both tables operate on Unicode code points for the second mapping and on raw
bytes for the first mapping; a Python port must preserve that distinction
(the first table is effectively ASCII-only).

## Implementation options

### Option A: full renderer (parity with StarDict)

Port the CDATA scanner, element handling, inline markup and both phonetic
tables, then emit HTML (`defiFormat = "h"`). This is the only option that
produces output comparable to StarDict. Estimated size: 250–350 lines plus
tests.

### Option B: text extraction

Parse the CDATA payloads, drop XML tags and inline markup, and emit plain text
(`defiFormat = "m"`). Much smaller (roughly 40–80 lines), but loses emphasis,
phonetic rendering, linked words and example formatting.

### Option C: raw XML to HTML

Try to normalise the fragment and convert it with a generic XML-to-HTML step.
Rejected: the data is not well-formed XML and the inline `&{…}` markup lives
inside CDATA, so a generic converter would render the markup literally.

## Why it was not added now

- It is a niche vendor-specific format.
- Correct output requires porting two custom phonetic tables and a non-XML
  inline markup parser, including Pango-to-HTML attribute mapping.
- It is still a sizeable amount of new logic.
- An incomplete implementation would silently produce worse definitions than
  the current "unsupported type" warning.

If support is added later, Option A is recommended, with synthetic test
fixtures that exercise old and new element names, CDATA variants, inline
markup nesting and both phonetic tables.
