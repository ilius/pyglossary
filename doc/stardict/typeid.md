# StarDict type identifiers

Single-character type identifiers used with the `sametypesequence` option in
the `.idx` file, or appearing in the `.dict` file when that option is not used.

Lower-case characters signify that a field's size is determined by a
terminating `'\0'`, while upper-case characters indicate that the data begins
with a network byte-ordered guint32 giving the length of the following data
(NOT the whole size, which is 4 bytes bigger).

## Overview

| ID | Data | Format | PyGlossary |
| -- | ---- | ------ | ---------- |
| `m` | Word's pure text meaning | utf-8 string ending with `'\0'` | ✅ |
| `h` | Html codes | text | ✅ |
| `x` | utf-8 string marked up with xdxf language | utf-8 string ending with `'\0'` | ✅ |
| `r` | Resource file list (`img:`, `snd:`, `vdo:`, `att:` lines) | utf-8 string ending with `'\0'`, `'\n'` separating lines | ✅ |
| `g` | utf-8 string marked up with Pango text markup language | utf-8 string ending with `'\0'` | ✅ |
| `t` | English phonetic string | utf-8 string ending with `'\0'` | ✅ |
| `y` | Chinese YinBiao or Japanese KANA | utf-8 string ending with `'\0'` | ✅ |
| `l` | Word's pure text meaning in locale encoding (discouraged) | string in locale encoding, ending with `'\0'` | ❌ |
| `k` | KingSoft PowerWord's data (XML format) | utf-8 string ending with `'\0'` | ❌ |
| `w` | MediaWiki markup language | text | ❌ |
| `n` | WordNet data | text | ❌ |
| `W` | wav file | guint32 length prefix, then file content | ❌ |
| `P` | Picture file | guint32 length prefix, then file content | ❌ |
| `X` | Reserved for experimental extensions | — | ❌ |

The PyGlossary column indicates whether the reader can decode the type.
When writing, PyGlossary only emits `m`, `h` and `x` (selectable with the
`sametypesequence` write option).

## Using the `sametypesequence` option

To convert to a StarDict dictionary with the `sametypesequence` option, use
`sametypesequence=[type of definitions]` write option.

If the sametypesequence option is set, it tells StarDict that each word's data
in the `.dict` file will have the same sequence of datatypes. Suppose a
dictionary contains phonetic information and a meaning for each word. The
sametypesequence option for this dictionary would be:

```
sametypesequence=tm
```

Examples:

Definitions type is plain text:

```
pyglossary mydic.txt mydic.ifo --write-options=sametypesequence=m
```

Definitions type is HTML:

```
pyglossary mydic.txt mydic.ifo --write-options=sametypesequence=h
```

## Details

### `m`

Word's pure text meaning.
The data should be a utf-8 string ending with `'\0'`.

### `h`

Html codes.

### `x`

A utf-8 string which is marked up with the [xdxf language](https://github.com/soshial/xdxf_makedict).<br/>
StarDict has these extensions:

- `<rref>` can have "type" attribute, it can be "image", "sound", "video"
  and "attach".
- `<kref>` can have "k" attribute.

### `r`

Resource file list.<br/>
The content can be:

- `img:pic/example.jpg` Image file
- `snd:apple.wav` Sound file
- `vdo:film.avi` Video file
- `att:file.bin` Attachment file

More than one line is supported as a list of available files.<br/>
StarDict will find the files in the Resource Storage.<br/>
The image will be shown, the sound file will have a play button.<br/>
You can "save as" the attachment file and so on.<br/>
The file list must be a utf-8 string ending with `'\0'`.<br/>
Use `'\n'` for separating new lines.<br/>
Use `/` character as directory separator.

### `g`

A utf-8 string which is marked up with the Pango text markup language.<br/>
For more information about this markup language, see the
[Pango Reference Manual](http://library.gnome.org/devel/pango/stable/PangoMarkupFormat.html).<br/>
You might have it installed locally \[here\](file:///usr/share/gtk-doc/html/pango/PangoMarkupFormat.html)

PyGlossary maps this type to `h` (HTML).

### `t`

English phonetic string.<br/>
The data should be a utf-8 string ending with `'\0'`.

Here are some utf-8 phonetic characters:<br/>
`θʃŋʧðʒæıʌʊɒɛəɑɜɔˌˈːˑṃṇḷ`<br/>
`æɑɒʌәєŋvθðʃʒɚːɡˏˊˋ`

PyGlossary maps this type to `m` (plain text).

### `y`

Chinese YinBiao or Japanese KANA.<br/>
The data should be a utf-8 string ending with `'\0'`.

PyGlossary maps this type to `m` (plain text).

### `l`

Word's pure text meaning.<br/>
The data is NOT a utf-8 string, but is instead a string in locale encoding,
ending with `'\0'`. Sometimes using this type will save disk space, but its use
is discouraged. This is only an idea.

### `k`

[KingSoft](https://en.wikipedia.org/wiki/Kingsoft) [PowerWord](https://en.wikipedia.org/wiki/PowerWord)'s data.
The data is a utf-8 string ending with `'\0'`. And it's in XML format.

### `w`

[MediaWiki markup language](https://www.mediawiki.org/wiki/Help:Formatting).

### `n`

WordNet data.

### `W`

`.wav` audio file.<br/>
The data begins with a network byte-ordered guint32 to identify the wav
file's size, immediately followed by the file's content.
This is only an idea, it is better to use `r` Resource file list in most
cases.

### `P`

Picture file.<br/>
The data begins with a network byte-ordered guint32 to identify the picture
file's size, immediately followed by the file's content.<br/>
This feature is implemented, as stardict-advertisement-plugin needs it.
Anyway, it is better to use `r` Resource file list in most cases.

### `X`

This type identifier is reserved for experimental extensions.

## For more information

Refer to StarDict documentations at:
[https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat](https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat)
