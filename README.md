PyGlossary
==========

PyGlossary is a tool for converting dictionary files aka glossaries,
from/to various formats used by different dictionary applications

Screenshots
-----------

<img src="https://raw.githubusercontent.com/ilius/pyglossary/resources/screenshots/32-gtk-bgl-stardict-aryanpur-dark.png" height="450"/>

Linux - Gtk3-based intreface

------------------------------------------------------------------------

<img src="https://raw.githubusercontent.com/ilius/pyglossary/resources/screenshots/32-tk-bgl-kobo-es-en.png" height="450"/>

Windows - Tkinter-based interface

------------------------------------------------------------------------

![](https://raw.githubusercontent.com/ilius/pyglossary/resources/screenshots/32-cmd-bgl-apple-ru-de.png)

Linux - command line interface

Supported formats
-----------------

| Format                            | Extension     | Read  | Write |
|-----------------------------------|---------------|:-----:|:-----:|
| Aard 2 (slob)                     | .slob         |   ✔   |   ✔   |
| ABBYY Lingvo DSL                  | .dsl          |   ✔   |       |
| AppleDict Binary                  | .dictionary   |   ✔   |       |
| AppleDict Source                  | .xml          |       |   ✔   |
| Babylon                           | .bgl          |   ✔   |       |
| Babylon Source                    | .gls          |       |   ✔   |
| CC-CEDICT                         |               |   ✔   |       |
| CSV                               | .csv          |   ✔   |   ✔   |
| DictionaryForMIDs                 |               |   ✔   |   ✔   |
| DICTD dictionary server           | .index        |   ✔   |   ✔   |
| Editable Linked List of Entries   | .edlin        |   ✔   |   ✔   |
| EPUB-2 E-Book                     | .epub         |       |   ✔   |
| FreeDict                          | .tei          |   ✔   |   ✔   |
| Gettext Source                    | .po           |   ✔   |   ✔   |
| Kobo E-Reader Dictionary          | .kobo.zip     |       |   ✔   |
| Kobo E-Reader Dictfile            | .df           |       |   ✔   |
| Lingoes Source                    | .ldf          |   ✔   |   ✔   |
| Octopus MDict                     | .mdx          |   ✔   |       |
| Octopus MDict Source              | .txt          |   ✔   |   ✔   |
| Sdictionary Binary                | .dct          |   ✔   |       |
| Sdictionary Source                | .sdct         |       |   ✔   |
| SQL                               | .sql          |       |   ✔   |
| StarDict                          | .ifo          |   ✔   |   ✔   |
| Tabfile                           | .txt, .dic    |   ✔   |   ✔   |
| TreeDict                          |               |       |   ✔   |
| XDXF                              | .xdxf         |   ✔   |       |


Requirements
------------

PyGlossary requires **Python 3.6 or higher**, and works in practically all
modern operating systems. While primarilly designed for *GNU/Linux*, it works
on *Windows*, *Mac OS X* and other Unix-based operating systems as well.

As shown in the screenshots, there are multiple User Interface types,
ie. multiple ways to use the program.

-	**Gtk3-based interface**, uses [PyGI (Python Gobject Introspection)](http://pygobject.readthedocs.io/en/latest/getting_started.html)
	You can install it on:
	-	Debian/Ubuntu: `apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
	-	openSUSE: `zypper install python3-gobject gtk3`
	-	Fedora: `dnf install pygobject3 python3-gobject gtk3`
	-	Archlinux:
		* `pacman -S python-gobject gtk3`
		* https://aur.archlinux.org/packages/pyglossary/
	-	Mac OS X: `brew install pygobject3 gtk+3`
	-	Nix / NixOS: `nix-shell -p gnome3.gobjectIntrospection python37Packages.pygobject3 python37Packages.pycairo`

-	**Tkinter-based interface**, works in the lack of Gtk. Specially on
	Windows where Tkinter library is installed with the Python itself.
	You can also install it on:
	-	Debian/Ubuntu: `apt-get install python3-tk tix`
	-	openSUSE: `zypper install python3-tk tix`
	-	Fedora: `yum install python3-tkinter tix`
	-	Mac OS X: read <https://www.python.org/download/mac/tcltk/>
	-	Nix / NixOS: `nix-shell -p python37Packages.tkinter tix`

-	**Command-line interface**, works in all operating systems without
	any specific requirements, just type:

	`python3 main.py --help`

	You may have to give `--no-progress-bar` option in Windows when
	converting glossaries (because the progress bar does not work
	properly in Windows command window)

When you run the program without any command line arguments or options,
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

-	**Reading from FreeDict or XDXF**

	`sudo pip3 install lxml`

-	**Reading from Babylon BGL**: Python 3.6 to 3.7 is recommended

-   **Reading from CC-CEDICT**

    `sudo pip3 install jinja2`

-	**Reading from Octopus Mdict (MDX)**

	+ **python-lzo**, required for **some** MDX glossaries

		- First try converting your MDX file, and if failed (`AssertionError` probably), then you may need to install LZO library and Python binding:

		- **On Linux**, make sure `liblzo2-dev` or `liblzo2-devel` is installed and then run `sudo pip3 install python-lzo`

		- **On Windows**:
			+ Open this page: https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo
			+ If you are using Python 3.7 (32 bit) for example, click on `python_lzo‑1.12‑cp37‑cp37m‑win32.whl`
			+ Open Start -> type Command -> right-click on Command Prompt -> Run as administrator
			+ Run `pip install C:\....\python_lzo‑1.12‑cp37‑cp37m‑win32.whl` command, giving the path of downloaded file


-	**Reading or writing Aard 2 (.slob) files**

	`sudo pip3 install PyICU`

-	**Writing to Kobo E-Reader Dictionary**

	`sudo pip3 install marisa-trie`


AppleDict
---------
See [doc/apple.md](doc/apple.md) for AppleDict requirements and instructions.


