# Tabfile format specification

Tabfile is a plain-text glossary: each **non-empty** line is one entry, with the **headword** and **definition** separated by the **first tab** (`U+0009`) on that line. Everything after that first tab is the definition, including any further tab characters. Lines with no tab are skipped on read (with a warning).

PyGlossary reads and writes this layout with optional **glossary info** lines at the top, **escaped** special characters, optional **resource files**, and optional **multipart** output.

Plugin overview and options: [Tabfile (.txt, .dic)](./p/tabfile.md).

## Encoding and line endings

The file is decoded with the `encoding` read/write option (default UTF-8). The writer ends each record with a newline (`\n`).

## Glossary info (metadata)

When `enable_info` is true on write (as it is by default), each glossary info field is written as one line: two `#` characters, the key, a tab, then the value — for example `##name\tMy dictionary` (with NTB escaping applied to key and value; see below).

On read, a **contiguous block of lines at the beginning of the file** whose headword **starts with `#`** after unescaping is treated as metadata: leading `#` characters are stripped from the key, and the pair is stored as glossary info. The first line that is not an info line starts normal entries (that line is not skipped).

## NTB escaping (newlines, tabs, backslashes)

Headwords and definitions are written with backslash escapes so tabs and newlines do not break the line structure. In the file you will see:

- `\t` for a literal tab, `\n` for a newline
- `\\` for a literal backslash (written as `\\` in the file, i.e. doubled)
- carriage returns are stripped on write

Implementation: `escapeNTB` / `unescapeNTB` in `pyglossary/text_utils.py`.

## Alternative headwords (`alts`)

If the glossary is configured with **alternatives** enabled when reading (as it is by default), the headword column may list several forms separated by `|` (only `|` not preceded by `\` starts a new segment). A literal bar is `\|`. Each segment is NTB-unescaped. With alternatives disabled, `|` is not treated as a separator.

## Resource directory

When `resources` is enabled on write, binary resources are stored under `<filename>_res/` next to the glossary file. On read, if `<filename>_res` exists (or `<path-without-compression-suffix>_res` for compressed inputs), files under that tree are loaded as resource entries.

## Multipart glossaries

If the glossary info includes `file_count` metadata/info key, the reader may continue with further parts until all are read. Each part is named by appending `.<n>` to the **full path of the file you opened first** (`n` is 1 for the second part, 2 for the third, and so on). If that path is not found, the reader also tries the same stem with each known compression extension (for example `.gz`).

Examples (three parts total, `file_count` `3`):

- Plain: open `myglossary.txt`, then also load `myglossary.txt.1` and `myglossary.txt.2`.
- With directory: open `dicts/en-fr.tab`, then `dicts/en-fr.tab.1` and `dicts/en-fr.tab.2`.
- Compressed first file: open `data/words.tsv.gz`; the next part is `data/words.tsv.gz.1`, or `data/words.tsv.gz.1.gz` (or another supported compression) if you split the continuations as separate compressed files.

## Compressed inputs

The tabfile reader accepts the same stream compressions as other text plugins (for example `.gz`, `.bz2`, `.lzma`).

## Write-only behaviour

- **`word_title`:** When true, the writer prepends a short headword title line to each definition, using the glossary’s word-title formatting.
- **`file_size_approx`:** When non-zero, output is split across multiple files when approximate size limits are reached; see glossary info `file_count` for readers.
