PyGlossary
==========

PyGlossary is a tool for converting dictionary files aka glossaries,
from/to various formats used by different dictionary applications

Screenshots
-----------

![](https://raw.githubusercontent.com/ilius/pyglossary/resources/screenshots/30-gtk-bgl-apple-nl-en.png)

Linux - (New) Gtk3-based intreface

------------------------------------------------------------------------

![](https://raw.githubusercontent.com/ilius/pyglossary/resources/screenshots/30-tk-bgl-mdict-fr-zh.png)

Linux - Tkinter-based interface

------------------------------------------------------------------------

![](https://raw.githubusercontent.com/ilius/pyglossary/resources/screenshots/30-cmd-bgl-txt-ru-de.png)

Linux - command line interface

Supported formats
-----------------

| Format                            | Extension     | Read  | Write  |
|-----------------------------------|---------------|-------|--------|
| ABBYY Lingvo DSL                  | .dsl          | X     |        |
| AppleDict Source                  | .xml          |       | X      |
| Babylon                           | .bgl          | X     |        |
| Babylon Source                    | .gls          |       | X      |
| CSV                               | .csv          | X     | X      |
| DictionaryForMIDs                 |               | X     | X      |
| DICTD dictionary server           | .index        | X     | X      |
| Editable Linked List of Entries   | .edlin        | X     | X      |
| FreeDict                          | .tei          |       | X      |
| Gettext Source                    | .po           | X     | X      |
| Lingoes Source (LDF)              | .ldf          | X     | X      |
| Octopus MDict                     | .mdx          | X     |        |
| Octopus MDict Source              | .txt          | X     | X      |
| Omnidic                           |               | X     | X      |
| Sdictionary Binary                | .dct          | X     |        |
| Sdictionary Source                | .sdct         |       | X      |
| SQL                               | .sql          |       | X      |
| SQLite 3                          | .sqlite       | X     | X      |
| StarDict                          | .ifo          | X     | X      |
| Tabfile                           | .txt, .dic    | X     | X      |
| TreeDict                          |               |       | X      |
| XDXF                              | .xdxf         | X     |        |
| xFarDic                           | .xdb          | X     | X      |


Requirements
------------

PyGlossary uses **Python 3.x**, and works in practically all operating
systems. While primarilly designed for *GNU/Linux*, it works on *Windows*,
*Mac OS X* and other Unix-based operating systems as well.

As shown in the screenshots, there are multiple User Interface types,
ie. multiple ways to use the program.

-   **Gtk3-based interface**, uses PyGI (Python Gobject Introspection)
    You can install it on:
    -   Debian: `apt-get install python3-gi`
    -   openSUSE: `zypper install python3-gobject`
    -   Fedora: `yum install python3-gobject`
    -   Archlinux: `pacman -S python-gobject`

-   **Tkinter-based interface**, works in the lack of Gtk. Specially on
    Windows where Tkinter library is installed with the Python itself.
    You can also install it on:
    -   Debian: `apt-get install python-tk tix`
    -   openSUSE: `zypper install tkinter tix`
    -   Fedora: `yum install tkinter tix`
    -   Mac OS X: read <https://www.python.org/download/mac/tcltk/>

-   **Command-line interface**, works in all operating systems without
    any specific requirements, just type:

    `python3 pyglossary.pyw --help`

    You may have to give `--no-progress-bar` option in Windows when
    converting glossaries (becouse the progress bar does not work
    properly in Windows command window)

When you run the program without any command line arguments or options,
PyGlossary tries to find PyGI, if it's installed, opens the Gtk3-based
interface, if it's not, tries to find Tkinter and open the Tkinter-based
interface. And exits with an error if neither are installed.

But you can explicitly determine the user interface type using `--ui`,
for example:

> `python3 pyglossary.pyw --ui=gtk`
>
> `python3 pyglossary.pyw --ui=tk`


Format-specific Requirements
----------------------------

-   **Writing to AppleDict**

    `sudo easy_install3 beautifulsoup4 html5lib`

-   **Reading from Octopus Mdict (MDX)**

    `sudo pip3 install python-lzo`


**Other Requirements for Mac OS X**

If you want to convert glossaries into AppleDict format on Mac OS X,
you also need:

-   GNU make as part of [Command Line Tools for
    Xcode](http://developer.apple.com/downloads).
-   Dictionary Development Kit as part of [Auxillary Tools for
    Xcode](http://developer.apple.com/downloads). Extract to
    `/Developer/Extras/Dictionary Development Kit`

HOWTOs
------

### Convert Babylon (bgl) to Mac OS X dictionary

Let's assume the Babylon dict is at
`~/Documents/Duden_Synonym/Duden_Synonym.BGL`:

    cd ~/Documents/Duden_Synonym/
    python ~/Software/pyglossary/pyglossary.pyw --read-options=resPath=OtherResources --write-format=AppleDict Duden_Synonym.BGL Duden_Synonym.xml
    make
    make install

Launch Dictionary.app and test.

### Convert Octopus Mdict to Mac OS X dictionary

Let's assume the MDict dict is at
`~/Documents/Duden-Oxford/Duden-Oxford DEED ver.20110408.mdx`.

Run the following command:

    cd ~/Documents/Duden-Oxford/
    python ~/Software/pyglossary/pyglossary.pyw --read-options=resPath=OtherResources --write-format=AppleDict "Duden-Oxford DEED ver.20110408.mdx" "Duden-Oxford DEED ver.20110408.xml"
    make
    make install

Launch Dictionary.app and test.


Let's assume the MDict dict is at `~/Downloads/oald8/oald8.mdx`, along
with the image/audio resources file `oald8.mdd`.

Run the following commands: :

    cd ~/Downloads/oald8/
    python ~/Software/pyglossary/pyglossary.pyw --read-options=resPath=OtherResources --write-format=AppleDict oald8.mdx oald8.xml

This extracts dictionary into `oald8.xml` and data resources into folder
`OtherResources`. Hyperlinks use relative path. :

    sed -i "" 's:src="/:src=":g' oald8.xml

Convert audio file from SPX format to WAV format. You need package
`speex` from [MacPorts](https://www.macports.org) :

    find OtherResources -name "*.spx" -execdir sh -c 'spx={};speexdec $spx  ${spx%.*}.wav' \;
    sed -i "" 's|sound://\([/_a-zA-Z0-9]*\).spx|\1.wav|g' oald8.xml

But be warned that the decoded WAVE audio can consume \~5 times more disk
space!

Compile and install. :

    make
    make install

Launch Dictionary.app and test.
