## StarDict (.ifo)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/stardict/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute | Value |
| --------- | ----- |
| Name | Stardict |
| snake_case_name | stardict |
| Description | StarDict (.ifo) |
| Extensions | `.ifo` |
| Read support | Yes |
| Write support | Yes |
| Single-file | No |
| Kind | 📁 directory |
| Sort-on-write | Always |
| Sort key | `stardict` |
| Wiki | [StarDict](https://en.wikipedia.org/wiki/StarDict) |
| Website | [huzheng.org/stardict](http://huzheng.org/stardict/) |

### Read options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| xdxf_to_html | `True` | bool | Convert XDXF entries to HTML |
| xsl | `False` | bool | Use XSL transformation |
| unicode_errors | `strict` | str | What to do with Unicode decoding errors |

### Write options

| Name | Default | Type | Comment |
| ---- | ------- | ---- | ------- |
| large_file | `False` | bool | Use idxoffsetbits=64 bits, for large files only |
| dictzip | `False` | bool | Compress .dict file to .dict.dz |
| dictzip_syn | `False` | bool | Compress .syn file to .syn.dz |
| sametypesequence |  | str | Definition format: h=html, m=plaintext, x=xdxf |
| stardict_client | `False` | bool | Modify html entries for StarDict 3.0 |
| audio_goldendict | `False` | bool | Convert audio links for GoldenDict (desktop) |
| audio_icon | `True` | bool | Add glossary's audio icon |
| autosqlite | `True` | bool | Auto-enable/disable SQLite option based on global SQLite mode. |
| sqlite | `False` | bool | Use SQLite to limit memory usage. |
| max_file_size | `0` | int | Max .dict file size before splitting into multiple glossaries;<br />0 means use default based on large_file (4 GiB or 64-bit limit).<br /> Examples: 100m, 1g |

### StarDict program HTML support

The StarDict application renders HTML definitions with a very limited engine
(its `stardict-html-parsedata-plugin`). It only understands these tags:

- inline formatting: `b`, `big`, `i`, `s`, `sub`, `sup`, `small`, `tt`, `u`,
  `font` (`face` and `color` attributes)
- line breaks: `br` (literal `<br>` only) and `hr`
- links and images: `a` (`href`), `img` (`src`)

All other tags — including `div`, `p`, `span`, `ol`, `li`, `blockquote`,
`table` and headings — are dropped and their content is rendered inline. As a
result:

- line breaks and block boundaries (keyword, sibling definitions, examples)
  are lost,
- ordered and unordered lists are not numbered or bulleted,
- `blockquote` indentation is not applied,
- the self-closing `<br/>` form is **not** recognized as a line break.
  PyGlossary emits `<br/>` by default, so explicit line breaks are dropped
  unless the `stardict_client` option is enabled, which rewrites them as
  `<br>` before writing,
- inline formatting (bold, italic, underline, sub/superscript, `font` color)
  is preserved.

This matters for `sametypesequence=h` (HTML) and `sametypesequence=x` (XDXF)
entries, which PyGlossary converts to HTML on read (see the `xdxf_to_html`
option). That HTML relies on `div`, `ol`/`li` and `<br/>` for layout, so
entries will look degraded in the StarDict program even with `stardict_client`
enabled (it only fixes line breaks). Viewers that support a larger HTML subset,
such as GoldenDict or AyanDict, are recommended instead.

See the
[StarDict HTML parsing plugin source](https://github.com/huzheng001/stardict-3/blob/master/dict/stardict-plugins/stardict-html-parsedata-plugin/stardict_html_parsedata.cpp).

### Dictionary Applications/Tools

| Name & Website | Source code | License | Platforms | Language |
| -------------- | ----------- | ------- | --------- | -------- |
| [AyanDict](https://github.com/ilius/ayandict) | [@ilius/ayandict](https://github.com/ilius/ayandict) | GPL | Linux, Windows, Mac | Go |
| [GoldenDict-NG by @xiaoyifang](https://xiaoyifang.github.io/goldendict-ng/) | [@xiaoyifang/goldendict-ng](https://github.com/xiaoyifang/goldendict-ng) | GPL | Linux, Windows, Mac | C++ |
| [GoldenDict](http://goldendict.org/) | [@goldendict/goldendict](https://github.com/goldendict/goldendict) | GPL | Linux, Windows, Mac | C++ |
| [SilverDict](https://silverdict.lecoteauverdoyant.co.uk/) | [@Crissium/SilverDict](https://github.com/Crissium/SilverDict) | GPL | Web | Python |
| [StarDict](http://huzheng.org/stardict/) | [@huzheng001/stardict-3](https://github.com/huzheng001/stardict-3) | GPL | Linux, Windows, Mac | C++ |
| [QStarDict](https://github.com/a-rodin/qstardict) | [@a-rodin/qstardict](https://github.com/a-rodin/qstardict) | GPLv2 | Linux, Windows, Mac | C++ |
| [KOReader](http://koreader.rocks/) | [@koreader/koreader](https://github.com/koreader/koreader) | AGPLv3 | Android, Amazon Kindle, Kobo eReader, PocketBook, Cervantes | Lua |
| [sdcv (command line)](https://dushistov.github.io/sdcv/) | [@Dushistov/sdcv](https://github.com/Dushistov/sdcv) | GPLv2 | Linux, Windows, Mac, Android | C++ |
| [QDict](https://f-droid.org/packages/com.annie.dictionary.fork/) | [@namndev/QDict](https://github.com/namndev/QDict) | Apache 2.0 | Android | Java |
| [GoldenDict Mobile (Free)](http://goldendict.mobi/) | ― | Proprietary (Freemium) | Android |  |
| [GoldenDict Mobile (Full)](http://goldendict.mobi/) | ― | Proprietary | Android |  |
| [WordMateX](https://apkcombo.com/wordmatex/org.d1scw0rld.wordmatex/) | ― | Proprietary | Android |  |
| [Fora Dictionary](https://play.google.com/store/apps/details?id=com.ngc.fora) | ― | Proprietary (Freemium) | Android |  |
| [Fora Dictionary Pro](https://play.google.com/store/apps/details?id=com.ngc.fora.android) | ― | Proprietary | Android |  |

### Related Formats

- [StarDict Textual File (.xml)](./stardict_textual.md)
- [StarDict (Merge Syns)](./stardict_merge_syns.md)
