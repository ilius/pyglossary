PyGlossary
==========

A tool for converting dictionary files aka glossaries.

The primary purpose is to be able to use our offline glossaries in any Open
Source dictionary we like on any OS/device.

There are countless formats, and my time is limited, so I implement formats that
seem more useful for myself, or for Open Source community. Also diversity of
languages is taken into account. Pull requests are welcome.

Screenshots
-----------

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40a-gtk-txt-stardict-aryanpour-dark.png" width="50%" height="50%"/>

Linux - Gtk3-based interface

------------------------------------------------------------------------

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40b-tk-bgl-epub-es-en-2.png" width="50%" height="50%"/>

Windows - Tkinter-based interface

------------------------------------------------------------------------

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/32-cmd-freedict-mids-de-ru.png" width="50%" height="50%"/>

Linux - command-line interface

------------------------------------------------------------------------

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40-cmdi-termux-zim-slob-en-med.jpg" width="50%" height="50%"/>

Android Termux - interactive command-line interface


Supported formats
-----------------

| Format                                                                |   |    Extension    |Read|Write|
|-----------------------------------------------------------------------|:-:|:---------------:|:--:|:---:|
| [Aard 2 (slob)](http://aarddict.org)                                  |🔢 | .slob           | ✔  |  ✔  |
| [ABBYY Lingvo](https://www.lingvo.ru/) DSL (Russian-origin)           |📝 | .dsl            | ✔  |     |
| Almaany.com (SQLite3, Arabic)                                         |🔢 | .db             | ✔  |     |
| AppleDict Binary                                                      |🔢 |.dictionary      | ✔  | ❌  |
| AppleDict Source                                                      |📁 |                 |    |  ✔  |
| Babylon                                                               |🔢 | .bgl            | ✔  | ❌  |
| [CC-CEDICT](https://cc-cedict.org/wiki) (Chinese)                     |📝 |                 | ✔  | ❌  |
| [cc-kedict](https://github.com/mhagiwara/cc-kedict) (Korean)          |📝 |                 | ✔  | ❌  |
| CSV                                                                   |📝 | .csv            | ✔  |  ✔  |
| [Dict.cc](https://ply.gl/cc.dict.dictcc) (SQLite3, German)            |🔢 | .db             | ✔  |     |
| DICT.org / Dictd server                                               |📁 | (📝.index)      | ✔  |  ✔  |
| DICT.org / dictfmt source file                                        |📝 | (.dtxt)         |    |  ✔  |
| [dictunformat](https://linux.die.net/man/1/dictunformat) output file  |📝 | (.dictunformat) | ✔  |     |
| [DictionaryForMIDs](http://dictionarymid.sourceforge.net)             |📁 | (📁.mids)       | ✔  |  ✔  |
| [DigitalNK](https://github.com/digitalprk/dicrs) (SQLite3, N-Korean)  |🔢 | .db             | ✔  |     |
| EDLIN                                                                 |📁 | .edlin          | ✔  |  ✔  |
| EPUB-2 E-Book                                                         |📦 | .epub           | ❌ |  ✔  |
| [FreeDict](https://freedict.org)                                      |📝 | .tei            | ✔  |  ✔  |
| [Gettext Source](https://www.gnu.org/software/gettext)                |📝 | .po             | ✔  |  ✔  |
| HTML Directory (by file size)                                         |📁 |                 | ❌ |  ✔  |
| [JMDict](https://www.edrdg.org/jmdict/j_jmdict.html) (Japanese)       |📝 |                 | ✔  | ❌  |
| JSON                                                                  |📝 | .json           |    |  ✔  |
| Kobo E-Reader Dictionary                                              |📦 | .kobo.zip       | ❌ |  ✔  |
| [Kobo E-Reader Dictfile](https://github.com/pgaskin/dictutil)         |📝 | .df             | ✔  |  ✔  |
| [Lingoes Source](http://www.lingoes.net/en/dictionary/dict_format.php)|📝 | .ldf            | ✔  |  ✔  |
| Octopus MDict (Chinese-origin)                                        |🔢 | .mdx            | ✔  | ❌  |
| [Sdictionary Binary](http://swaj.net/sdict/)                          |🔢 | .dct            | ✔  |     |
| [Sdictionary Source](http://swaj.net/sdict/create-dicts.html)         |📝 | .sdct           |    |  ✔  |
| SQL                                                                   |📝 | .sql            | ❌ |  ✔  |
| [StarDict](https://github.com/huzheng001/stardict-3)                  |📁 | (📝.ifo)        | ✔  |  ✔  |
| [Tabfile](https://en.wikipedia.org/wiki/Tab-separated_values)         |📝 |.txt, .tab       | ✔  |  ✔  |
| [Wiktionary Dump](https://dumps.wikimedia.org/backup-index.html)      |📝 | .xml            | ✔  | ❌  |
| [Wordset.org](https://github.com/wordset/wordset-dictionary)          |📁 |                 | ✔  |     |
| [XDXF](https://github.com/soshial/xdxf_makedict)                      |📝 | .xdxf           | ✔  | ❌  |
| Zim ([Kiwix](https://github.com/kiwix))                               |🔢 | .zim            | ✔  |     |

Legend:
- 📁	Directory
- 📝	Text file
- 📦	Package/archive file
- 🔢	Binary file
- ✔		Supported
- ❌ 	Will not be supported

Note: SQLite3 `.db` files are not detected by extension, you need to specify the format.

Requirements
------------

PyGlossary requires **Python 3.7 or higher**, and works in practically all
modern operating systems. While primarily designed for *GNU/Linux*, it works
on *Windows*, *Mac OS X* and other Unix-based operating systems as well.

As shown in the screenshots, there are multiple User Interface types (multiple
ways to use the program).

-	**Gtk3-based interface**, uses [PyGI (Python Gobject Introspection)](http://pygobject.readthedocs.io/en/latest/getting_started.html)
	You can install it on:
	-	Debian/Ubuntu: `apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
	-	openSUSE: `zypper install python3-gobject gtk3`
	-	Fedora: `dnf install pygobject3 python3-gobject gtk3`
	-	ArchLinux:
		* `pacman -S python-gobject gtk3`
		* https://aur.archlinux.org/packages/pyglossary/
	-	Mac OS X: `brew install pygobject3 gtk+3`
	-	Nix / NixOS: `nix-shell -p gnome3.gobjectIntrospection python38Packages.pygobject3 python38Packages.pycairo`

-	**Tkinter-based interface**, works in the lack of Gtk. Specially on
	Windows where Tkinter library is installed with the Python itself.
	You can also install it on:
	-	Debian/Ubuntu: `apt-get install python3-tk tix`
	-	openSUSE: `zypper install python3-tk tix`
	-	Fedora: `yum install python3-tkinter tix`
	-	Mac OS X: read <https://www.python.org/download/mac/tcltk/>
	-	Nix / NixOS: `nix-shell -p python38Packages.tkinter tix`

-	**Command-line interface**, works in all operating systems without
	any specific requirements, just type:

	`python3 main.py --help`

	- **Interactive command-line interface**
		- Requires: `pip3 install prompt_toolkit`
		- Perfect for mobile devices (like Termux on Android) where no GUI is available
		- Automatically selected if output file argument is not passed **and** one of these:
			- On Linux and `$DISPLAY` environment variable is empty or not set
				- For example when you are using a remote Linux machine over SSH
			- On Mac and no `tkinter` module is found
		- Manually select with `--cmd` or `--ui=cmd`
			- Minimally: `python3 main.py --cmd`
			- You can still pass input file, or any flag/option
		- If both input and output files are passed, non-interactive cmd ui will be default
		- If you are writing a script, you can pass `--no-interactive` to force disable interactive ui
			- Then you have to pass both input and output file arguments
		- Don't forget to use *Up/Down* or *Tab* keys in prompts!
			- Up/Down key shows you recent values you have used
			- Tab key shows available values/options
		- You can press Control+C (on Linux/Windows) at any prompt to exit



When you run the program without any command-line arguments or options,
PyGlossary tries to find PyGI, if it's installed, opens the Gtk3-based
interface, if it's not, tries to find Tkinter and open the Tkinter-based
interface. And exits with an error if neither are installed.

But you can explicitly determine the user interface type using `--ui`,
for example:

	python3 main.py --ui=gtk

Or

	python3 main.py --ui=tk


Feature-specific Requirements
----------------------------

-	**Using `--remove-html-all` flag**

	`sudo pip3 install lxml beautifulsoup4`

-	**Reading from FreeDict, XDXF (or StarDict with XDXF), JMDict or CC-CEDICT**

	`sudo pip3 install lxml`

-	**Reading from cc-kedict**

	`sudo pip3 install lxml PyYAML`

-	**Reading or writing Aard 2 (.slob) files**

	`sudo pip3 install PyICU`

-	**Writing to Kobo E-Reader Dictionary**

	`sudo pip3 install marisa-trie`

-	**Reading from Zim** (see [#228](https://github.com/ilius/pyglossary/issues/228))

	`sudo pip3 install libzim`

-	**Reading from Octopus MDict (MDX)**

	`python-lzo` is required for **some** MDX glossaries.
	First try converting your MDX file, if failed (`AssertionError` probably),
	then try to install [LZO library and Python binding](doc/lzo.md).


**Using Termux on Android?** See [doc/termux.md](./doc/termux.md)


User Plugins
------------
If you want to add your own plugin without adding it to source code directory,
or you want to use a plugin that has been removed from repository,
you can place it in this directory:
- Linux: `~/.pyglossary/plugins/`
- Mac: `~/Library/Preferences/PyGlossary/plugins`
- Windows: `C:\Users\USERNAME\AppData\Roaming\PyGlossary\plugins`


AppleDict
---------
See [doc/apple.md](doc/apple.md) for AppleDict requirements and instructions.


Internal Glossary Structure
---------------------------
A glossary contains a number of entries.

Each entry contains:

- Headword (title or main phrase for query)
- Alternates (some alternative phrases for query)
- Definition

In PyGlossary, headword and alternates together are accessible as a single Python list `entry.l_word`

`entry.defi` is the definition as a Python Unicode `str`. Also `entry.b_defi` is definition in UTF-8 byte array.

`entry.defiFormat` is definition format. If definition is plaintext (not rich text), the value is `m`. And if it's in HTML (contains any html tag), then `defiFormat` is `m`. The value `x` is also allowed for XFXF, but XDXF is not widely supported in dictionary applications.

There is another type of `Entry` which is called **Data Entry**, and generally contains image files, TTL or other audio files, or any file that was included in input glossary. For data entries:
- `entry.s_word` is file name (and `l_word` is still a list containing this string),
- `entry.defiFormat` is `b`
- `entry.data` gives the content of file in `bytes`.

