# FreeDict plugin architecture

Design notes for the `freedict` plugin, which reads FreeDict TEI sources and
can produce either HTML (the default) or Markdown definitions through the
`defiFormat` read option. Both outputs share one parser, one layout pass, and one
generic formatter traversal; they differ only in the formatter subclass that
turns the neutral document into output.

## Goals

- Keep TEI knowledge in the parsing/layout layers only.
- Let formatters work on a small, neutral document model.
- Avoid duplicating the entry loop, XInclude handling, metadata, progress and
  option plumbing between output formats.
- Make adding another output format a matter of writing a new formatter.

## Design rules

These rules keep the layers from leaking into each other:

1. **The parser never produces output.** It returns parsed dataclasses and
   metadata; it does not know HTML, Markdown or formatter options beyond the
   language direction needed to populate attributes.
2. **The layout layer makes every structural decision.** Ordering, list
   wrapping, pending tags, sub-senses and example structure are resolved here,
   before a formatter runs.
3. **Formatters never reorder or group nodes.** They walk the tree in order and
   map each node to output syntax.
4. **Formatters do not import the parser.** They only import `document` nodes
   and implement the generic output methods.
5. **HtmlFormatter owns all HTML syntax.** It uses lxml `htmlfile`; MdFormatter
   owns all Markdown syntax and never emulates HTML tags.

## Pipeline

```text
Reader (freedict, defiFormat = h or m)
  -> Parser                TEI XML -> parsed TEI dataclasses
  -> layout.buildDocument  parsed dataclasses -> neutral document tree
  -> Formatter             neutral document tree -> generic node methods
  -> HtmlFormatter/MdFormatter  HTML (lxml) or Markdown output
```

The reader returns one glossary entry per TEI `<entry>`. The entry's headwords
come from the parser; its definition text comes from the formatter.

## Directory layout

```text
pyglossary/plugins/freedict/
  __init__.py        plugin registration (FreeDict)
  options.py         read options
  reader.py          Reader: file handling and entry loop; selects formatter
  parser.py          TEI -> parsed dataclasses, metadata
  layout.py          parsed dataclasses -> neutral document
  document.py        neutral document node definitions
  formatter.py       generic Formatter node dispatch
  html_formatter.py  HtmlFormatter
  md_formatter.py    MdFormatter
  utils.py           TEI helper functions
  README.md          this file
```

## Modules

| Module | Responsibility | TEI-aware |
| ------ | -------------- | --------- |
| `freedict/reader.py` | `Reader`: compression, byte progress, TEI header metadata, XInclude resolution/cycles, include chain, `iterparse` entry loop, option copying into included readers; selects `HtmlFormatter` or `MdFormatter` from the `defiFormat` option. | partly (iterparse tags) |
| `freedict/parser.py` | Parses TEI elements into `Entry`, `Sense`, `TransCit`, `ExampleCit`, `GramGroup`, `Tag`, `Block`, `Inline` dataclasses. Also parses metadata. | yes |
| `freedict/layout.py` | Converts parsed dataclasses into the neutral tree. Owns ordering decisions: pending usage/label tags, definition/note/translation lists, sub-senses, RTL sense lists, grammar grouping, example structure, comma separators and optional headword titles. | yes |
| `freedict/document.py` | Neutral node definitions used by all formatters. | no |
| `freedict/formatter.py` | `Formatter`: generic traversal of the neutral tree that dispatches each node to an output method. | no |
| `freedict/html_formatter.py` | `HtmlFormatter`: implements the node methods with lxml `htmlfile`, HTML tags and attributes. | no |
| `freedict/md_formatter.py` | `MdFormatter`: implements the node methods with Markdown syntax, lists and blockquotes. | no |
| `freedict/options.py` | Read options. | no |
| `freedict/utils.py` | TEI helpers: language description, RTL detection, title tag, serialization. | yes |

## Neutral document model

`document.py` defines two categories of nodes.

Inline nodes:

- `Text(text)` – literal text
- `LineBreak()` – a line break
- `Link(target, children)` – a link; `target` may be `None`
- `Tag(kind, children)` – usage or label badge (`kind` is `"usage"` or
  `"label"`)
- `Grammar(text)` – one grammar word
- `InlineElement(tag, attrib, children)` – transparent `<p>`, `<div>` or
  `<span>` passthrough

Block and semantic nodes:

- `Block(attrib, children)` – a generic block with attributes
- `ListBlock(ordered, items)` – ordered/unordered list; each item is a
  sequence of nodes
- `Example(children)` – an example block (HTML blockquote-style example)
- `Pronunciation(items, separators)` – pronunciation items and the separators
  to insert between them
- `Title(text)` – optional headword title

No node mentions TEI. For example, the layout layer decides that a sense's
usage tags share the line of its first translation; the formatter only sees
`Tag`, `Text(" ")` and `Block` nodes in the right order.

### Node reference

| Node | Fields | HTML formatting | Markdown formatting |
| ---- | ------ | -------------- | ------------------ |
| `Text` | `text` | written as-is | written as-is |
| `LineBreak` | – | `<br>` | line break |
| `Link` | `target`, `children` | `<a href="...">`; external URLs get `class="external"`; missing targets become `bword://text` | `[text](url)` |
| `Tag` | `kind`, `children` | `<span class="tag" style="...">[children]</span>`, colored by usage/label option | `**children**` |
| `Grammar` | `text` | `<font class="grammar" color="...">text</font>` | `*text*` |
| `InlineElement` | `tag`, `attrib`, `children` | element opened with the given tag/attributes | `<p>` adds paragraph breaks; `<div>`/`<span>` are transparent |
| `Block` | `attrib`, `children` | `<div>` with attributes | children in order |
| `ListBlock` | `ordered`, `items` | `<ol>`/`<ul>` with `<li>` per item | numbered or bulleted list, nested by depth |
| `Example` | `children` | `<div class="example" style="padding: ...">` | blockquote (`> ...`) |
| `Pronunciation` | `items`, `separators` | `/` + colored font + `/` per item, then `<br>` | `/pron/` per item |
| `Title` | `text` | `glos.titleTag(text)` element (or plain text), then `<br>` | bold/heading depending on the title tag |

`HtmlFormatter` wraps the whole document in an outer `<div>`; `MdFormatter`
does not add a wrapper.

## Worked example

Input TEI:

```xml
<entry xml:lang="en">
  <form>
    <orth>word</orth>
    <pron>wɜːd</pron>
  </form>
  <gramGrp><pos>n</pos></gramGrp>
  <sense xml:lang="de">
    <usg type="domain">archaic</usg>
    <def>a unit of language</def>
    <cit type="trans"><quote>Wort</quote></cit>
  </sense>
</entry>
```

The parser produces an `Entry` with keywords `["word"]`, pronunciation
`["wɜːd"]`, one grammar group (`["noun"]`) and one `Sense` containing a usage
tag, a definition and one translation citation.

`layout.buildDocument` turns that into roughly:

```text
Pronunciation(["wɜːd"], [])
Block([Grammar("noun")])
Tag("usage", [Text("archaic")])
Text(" ")
Text("a unit of language")
Block([Text("Wort")])
```

The flat `Tag`/`Text` sequence is intentional: it preserves the original
in-line flow, where the usage tag is followed by the definition on the same
line.

The HTML formatter then produces (wrapped here for readability):

```html
<div>/<font color="gray">wɜːd</font>/<br>
<div><font class="grammar" color="green">noun</font></div><span class="tag"
style="...">[archaic]</span> a unit of language<div>Wort</div></div>
```

The Markdown formatter walks the same nodes and produces:

```markdown
/wɜːd/

*noun***[archaic]** a unit of languageWort
```

The Markdown formatter only inserts line breaks where a node asks for one, so block
boundaries that HTML expresses with `<div>` are not automatically turned into
blank lines.

## Lifecycle

1. **Open.** `Reader.open(filename)` records the file name and directory,
   extends the real-path include chain, opens the compressed input, records
   `input_file_size`, sets up byte progress, sets the default definition format
   from the formatter's `defiFormat`, and reads the TEI header with `iterparse`.
2. **Metadata.** `Parser.parseMetadata` extracts the title, edition, copyright,
   publisher, creation time, description, website and entry count. `Reader`
   forwards them to the glossary via `setInfo` (with `unescape_unicode`).
3. **Iterate.** `Reader.__iter__` reopens the file and uses `iterparse`
   with `events=("end",)` for TEI entries and XInclude elements.
4. **Includes.** An XInclude element is resolved relative to the current
   file's directory. Missing files and already-visited real paths (cycles) are
   logged and skipped. A new reader of the same class is created, inherits the
   options and include chain, yields its entries, and is closed.
5. **Convert.** For each entry: parse -> build document -> format -> call
   `glos.newEntry(keywords, definition, defiFormat=..., byteProgress=...)`.
6. **Memory.** After each entry, `drop_previous_siblings` discards parsed XML
   nodes that will never be needed again.
7. **Close.** `Reader.close` closes the file and resets file state.

## Metadata

Parsed from the TEI header into `Metadata`, then applied to the glossary:

| Glossary info | Source |
| ------------- | ------ |
| `name` | TEI `<title>` |
| `edition` | TEI `<edition>` |
| `copyright` | availability paragraphs, with `<ref>` converted to links |
| `publisher` | TEI `<publisher>` |
| `creationTime` | publication date |
| `description` | source/project description paragraphs |
| `website` | `Home:` links in the description |
| `input_file_size` | size of the top-level input file |
| `definition_has_headwords` | set when `word_title` is enabled |

`entryCount` from the TEI header drives `__len__` and therefore progress
reporting when present.

## Formatting

`Formatter` in `freedict/formatter.py` contains the only traversal over document
nodes. It dispatches each node to a generic output method such as
`_writeBlock`, `_writeListBlock`, `_writeTag` or `_writeTitle`.

`HtmlFormatter` implements those methods with lxml `htmlfile`, HTML tags and
attributes: `<div>`, `<ol>`/`<ul>`, `<li>`, `<span>`, `<font>` and `<br>`.
`MdFormatter` implements the same methods directly with Markdown: numbered or
bullet lists, blockquotes, bold tags, italic grammar and Markdown links. It also
cleans up trailing spaces and collapses more than two consecutive newlines.

## Options

PyGlossary assigns read options to the reader as `_<option>` attributes. Each
layer reads the options it needs:

| Option | Default | Used by |
| ------ | ------- | ------- |
| `defiFormat` | `"h"` | reader (selects `HtmlFormatter` or `MdFormatter`) |
| `auto_rtl` | `True` | parser (language attributes), layout (RTL sense lists) |
| `auto_comma` | `True` | layout (grammar and pronunciation separators) |
| `comma` | `", "` | layout (fallback separator) |
| `word_title` | `False` | layout (whether to emit `Title` nodes) and reader (headword info flag) |
| `pron_color` | `gray` | formatter (pronunciation font) |
| `gram_color` | `green` | formatter (grammar font) |
| `usage_color` | `green` | formatter (usage tag background) |
| `label_color` | `darkblue` | formatter (label tag background) |
| `example_padding` | `10` | formatter (example block padding, in px) |

Included readers receive the same options through `Reader._copyOptionsTo`.

## Error handling

- Missing `lxml` at open time raises with an install hint (`pip install lxml`).
- A missing XInclude target is logged and skipped.
- An XInclude cycle is detected by real path and skipped.
- Unknown TEI elements and note/citation types are logged. Where possible their
  text is kept (for example as a note) instead of being dropped.
- Empty references (`<ref/>` with neither target nor text) are skipped.
- Non-seekable inputs disable byte progress with a warning.
- A TEI header without an `extent` element disables count-based progress with a
  warning.

## Performance notes

- Input is read incrementally with `iterparse`; the file is scanned twice, once
  for the header and once for entries.
- `drop_previous_siblings` keeps memory bounded for large dictionaries.
- BYTE progress uses the current file position and the top-level file size.
- Included files do not overwrite the top-level input size.

## Trade-offs

- HTML is the reference output. Markdown is produced from the same neutral tree
  through the same formatter methods, so both formats stay semantically aligned.
- Some document nodes are deliberately flat (`Tag`, `Text`, `Block` siblings)
  to preserve the original line flow without a second layout pass.
- The layout layer carries TEI-specific ordering knowledge. This keeps the
  parser focused on XML shape and the formatters focused on syntax.
- A new output format implements the generic formatter methods for the nodes
  it maps differently.

## Where to change what

| Change | File |
| ------ | ---- |
| TEI element parsing, grammar normalization, metadata | `parser.py` |
| Ordering, list decisions, tag placement, separators | `layout.py` |
| New neutral node | `document.py`, `layout.py`, `formatter.py` |
| HTML markup or styling | `html_formatter.py` |
| Markdown syntax | `md_formatter.py` |
| File handling, includes, metadata application | `reader.py` |
| Plugin metadata and options | `__init__.py`, `options.py` |

## Adding another output format

1. Create a `Formatter` subclass with a `defiFormat` and implementations of
   the generic node output methods.
2. Extend `Reader._newFormatter()` to select it from a new `defiFormat` option value.
3. Add the new value to the `defiFormat` option in `options.py`.

No parser or layout changes are needed unless the new format must represent
information that the neutral document model does not yet carry.

## Tests

Run the plugin suite from `tests`:

```sh
python -m unittest g_freedict_test.py
```

Coverage report for the plugin:

```sh
python scripts/test-cover-html-plugin.py freedict
```

Fixtures live under `tests/data/`; Markdown expectations are suffixed `-md`.
