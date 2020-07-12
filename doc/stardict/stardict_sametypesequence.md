To convert to a StarDict dictionary with the `sametypesequence` option, use
`sametypesequence=[type of defnitions]` write option.

If the sametypesequence option is set, it tells StarDict that each
word's data in the .dict file will have the same sequence of datatypes.
Suppose a dictionary contains phonetic information
and a meaning for each word.  The sametypesequence option for this
dictionary would be:

    sametypesequence=tm

# Examples:

Definitions type is plain text:

    pyglossary mydic.txt mydic.ifo --write-options=sametypesequence=m

Definitions type is HTML:

    pyglossary mydic.txt mydic.ifo --write-options=sametypesequence=h

# Type identifiers

Here are the single-character type identifiers that may be used with
the "sametypesequence" option in the .idx file, or may appear in the
dict file itself if the "sametypesequence" option is not used.

Lower-case characters signify that a field's size is determined by a
terminating `\0`, while upper-case characters indicate that the data
begins with a network byte-ordered guint32 that gives the length of 
the following data's size (NOT the whole size which is 4 bytes bigger).

## `m`
Word's pure text meaning.
The data should be a utf-8 string ending with `\0`.

## `l`
Word's pure text meaning.<br/>
The data is NOT a utf-8 string, but is instead a string in locale
encoding, ending with `\0`. Sometimes using this type will save disk
space, but its use is discouraged. This is only a idea.

## `g`
A utf-8 string which is marked up with the Pango text markup language.<br/>
For more information about this markup language, See the
[Pango Reference Manual](http://library.gnome.org/devel/pango/stable/PangoMarkupFormat.html).<br/>
You might have it installed locally [here](file:///usr/share/gtk-doc/html/pango/PangoMarkupFormat.html)


## `t`
English phonetic string.<br/>
The data should be a utf-8 string ending with `\0`.

Here are some utf-8 phonetic characters:<br/>
`θʃŋʧðʒæıʌʊɒɛəɑɜɔˌˈːˑṃṇḷ`<br/>
`æɑɒʌәєŋvθðʃʒɚːɡˏˊˋ`

## `x`
A utf-8 string which is marked up with the [xdxf language](https://github.com/soshial/xdxf_makedict).<br/>
StarDict has these extensions:

- `<rref>` can have "type" attribute, it can be "image", "sound", "video" 
and "attach".
- `<kref>` can have "k" attribute.

## `y`
Chinese YinBiao or Japanese KANA.<br/>
The data should be a utf-8 string ending with `\0`.

## `k`
[KingSoft](https://en.wikipedia.org/wiki/Kingsoft) [PowerWord](https://en.wikipedia.org/wiki/PowerWord)'s data.
The data is a utf-8 string ending with `\0`. And it's in XML format.

## `w`
[MediaWiki markup language](https://www.mediawiki.org/wiki/Help:Formatting).

## `h`
Html codes.

## `n`
WordNet data.

## `r`
Resource file list.<br/>
The content can be:
- `img:pic/example.jpg`	Image file
- `snd:apple.wav`		Sound file
- `vdo:film.avi`		Video file
- `att:file.bin`		Attachment file

More than one line is supported as a list of available files.<br/>
StarDict will find the files in the Resource Storage.<br/>
The image will be shown, the sound file will have a play button.<br/>
You can "save as" the attachment file and so on.<br/>
The file list must be a utf-8 string ending with `\0`.<br/>
Use `\n` for separating new lines.<br/>
Use `/` character as directory separator.<br/>

## `W`
`.wav` audio file.<br/>
The data begins with a network byte-ordered guint32 to identify the wav
file's size, immediately followed by the file's content.
This is only a idea, it is better to use `r` Resource file list in most
case.

## `P`
Picture file.<br/>
The data begins with a network byte-ordered guint32 to identify the picture
file's size, immediately followed by the file's content.<br/>
This feature is implemented, as stardict-advertisement-plugin needs it.
Anyway, it is better to use `r` Resource file list in most case.

## `X`
This type identifier is reserved for experimental extensions.

# For more information
Refer to StarDict documentations at:
[https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat](https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat)
