To convert to a stardict dictionary with the sametypesequence option use "sametypesequence=[type of defnitions]" write option.

If the sametypesequence option is set, it tells StarDict that each
word's data in the .dict file will have the same sequence of datatypes.
Suppose a dictionary contains phonetic information
and a meaning for each word.  The sametypesequence option for this
dictionary would be:

    sametypesequence=tm

### Examples:

Definitions type is plain text:

    pyglossary mydic.txt mydic.ifo --write-options=sametypesequence=m

Definitions type is HTML:

    pyglossary mydic.txt mydic.ifo --write-options=sametypesequence=h

Type identifiers
--
Here are the single-character type identifiers that may be used with
the "sametypesequence" option in the .idx file, or may appear in the
dict file itself if the "sametypesequence" option is not used.

Lower-case characters signify that a field's size is determined by a
terminating '\0', while upper-case characters indicate that the data
begins with a network byte-ordered guint32 that gives the length of 
the following data's size (NOT the whole size which is 4 bytes bigger).

'm'
Word's pure text meaning.
The data should be a utf-8 string ending with '\0'.

'l'
Word's pure text meaning.
The data is NOT a utf-8 string, but is instead a string in locale
encoding, ending with '\0'. Sometimes using this type will save disk
space, but its use is discouraged. This is only a idea.

'g'
A utf-8 string which is marked up with the Pango text markup language.
For more information about this markup language, See the "Pango
Reference Manual."
You might have it installed locally at:
file:///usr/share/gtk-doc/html/pango/PangoMarkupFormat.html
Online:
http://library.gnome.org/devel/pango/stable/PangoMarkupFormat.html

't'
English phonetic string.
The data should be a utf-8 string ending with '\0'.

Here are some utf-8 phonetic characters:
θʃŋʧðʒæıʌʊɒɛəɑɜɔˌˈːˑṃṇḷ
æɑɒʌәєŋvθðʃʒɚːɡˏˊˋ

'x'
A utf-8 string which is marked up with the xdxf language.
See http://xdxf.sourceforge.net
StarDict have these extension:
<rref> can have "type" attribute, it can be "image", "sound", "video" 
and "attach".
<kref> can have "k" attribute.

'y'
Chinese YinBiao or Japanese KANA.
The data should be a utf-8 string ending with '\0'.

'k'
KingSoft PowerWord's data. The data is a utf-8 string ending with '\0'.
It is in XML format.

'w'
MediaWiki markup language.
See http://meta.wikimedia.org/wiki/Help:Editing#The_wiki_markup

'h'
Html codes.

'n'
WordNet data.

'r'
Resource file list.
The content can be:
img:pic/example.jpg	// Image file
snd:apple.wav		// Sound file
vdo:film.avi		// Video file
att:file.bin		// Attachment file
More than one line is supported as a list of available files.
StarDict will find the files in the Resource Storage.
The image will be shown, the sound file will have a play button.
You can "save as" the attachment file and so on.
The file list must be a utf-8 string ending with '\0'.
Use '\n' for separating new lines.
Use '/' character as directory separator.

'W'
wav file.
The data begins with a network byte-ordered guint32 to identify the wav
file's size, immediately followed by the file's content.
This is only a idea, it is better to use 'r' Resource file list in most
case.

'P'
Picture file.
The data begins with a network byte-ordered guint32 to identify the picture
file's size, immediately followed by the file's content.
This feature is implemented, as stardict-advertisement-plugin needs it.
Anyway, it is better to use 'r' Resource file list in most case.

'X'
this type identifier is reserved for experimental extensions.

### For more information
Refer to StarDict documentations at:
[https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat](https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat)
