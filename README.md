# PyGlossary

<p align="center">
	<img src="https://raw.githubusercontent.com/ilius/pyglossary/refs/heads/master/res/pyglossary-256x256.png"></img>
</p>

[![PyPI](https://img.shields.io/pypi/v/pyglossary.svg)](https://pypi.org/project/pyglossary/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pyglossary)](https://pypi.org/project/pyglossary/)
[![tests](https://github.com/ilius/pyglossary/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/ilius/pyglossary/actions/workflows/test.yml?query=branch%3Amaster)

A tool for converting dictionary files, also known as glossaries.

Its primary purpose is to let you use offline glossaries in any Open Source
dictionary application, on any operating system or device.

There are countless formats and limited time, so PyGlossary implements the
formats that seem most useful to the author or to the Open Source community,
while also taking language diversity into account. Pull requests are welcome.

## Screenshots

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/52-gtk3-txt-stardict-aryanpur-dark2.png" width="50%" height="50%"/>

Linux - Gtk3-based interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/52-tk-dsl-stardict-windows-greek.png" width="50%" height="50%"/>

Windows - Tkinter-based interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/32-cmd-freedict-mids-de-ru.png" width="50%" height="50%"/>

Linux - command-line interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/40-cmdi-termux-zim-slob-en-med.jpg" width="50%" height="50%"/>

Android Termux - interactive command-line interface

______________________________________________________________________

<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/50-web-wiktextract-ifo-ar.png" width="50%" height="50%"/>

Web interface

## Supported formats

| Format | | Extension | Read | Write |
| ------------------------------------------------------- | :-: | :-------------: | :--: | :---: |
| [Aard 2 (slob)](./doc/p/aard2_slob.md) | 🔢 | .slob | ✅ | ✅ |
| [AppleDict Binary](./doc/p/appledict_bin.md) | 📁 | .dictionary | ✅ | ❌ |
| [AppleDict Source](./doc/p/appledict.md) | 📁 | | ✅ | ✅ |
| [Babylon BGL](./doc/p/babylon_bgl.md) | 🔢 | .bgl | ✅ | ✅ |
| [CSV](./doc/p/csv.md) | 📝 | .csv | ✅ | ✅ |
| [Dict.cc translation export](./doc/p/dict_cc_source.md) | 📝 | .txt | ✅ | ❌ |
| [DICT.org / Dictd server](./doc/p/dict_org.md) | 📁 | (📝.index) | ✅ | ✅ |
| [DICT.org / dictfmt source](./doc/p/dict_org_source.md) | 📝 | (.dtxt) | | ✅ |
| [dictunformat output file](./doc/p/dictunformat.md) | 📝 | (.dictunformat) | ✅ | |
| [DictionaryForMIDs](./doc/p/dicformids.md) | 📁 | (📁.mids) | ✅ | ✅ |
| [DIKT JSON](./doc/p/dikt_json.md) | 📝 | (.json) | | ✅ |
| [EPUB-2 E-Book](./doc/p/epub2.md) | 📦 | .epub | ❌ | ✅ |
| [FreeDict](./doc/p/freedict.md) | 📝 | .tei | ✅ | ❌ |
| [FreeDict Markdown](./doc/p/freedict_md.md) | 📝 | .tei | ✅ | ❌ |
| [Gettext Source](./doc/p/gettext_po.md) | 📝 | .po | ✅ | ✅ |
| [HTML Directory (by file size)](./doc/p/html_dir.md) | 📁 | | ❌ | ✅ |
| [JSON](./doc/p/json.md) | 📝 | .json | | ✅ |
| [Kobo E-Reader Dictionary](./doc/p/kobo.md) | 📦 | .kobo.zip | ❌ | ✅ |
| [Kobo E-Reader Dictfile](./doc/p/kobo_dictfile.md) | 📝 | .df | ✅ | ✅ |
| [Lingoes Source](./doc/p/lingoes_ldf.md) | 📝 | .ldf | ✅ | ✅ |
| [Mobipocket E-Book](./doc/p/mobi.md) | 🔢 | .mobi | ❌ | ✅ |
| [Octopus MDict](./doc/p/octopus_mdict.md) | 🔢 | .mdx | ✅ | ❌ |
| [PocketBook SDIC](./doc/p/pocketbook_sdic.md) | 🔢 | .dic | ❌ | ✅ |
| [QuickDic version 6](./doc/p/quickdic6.md) | 🔢 | .quickdic | ✅ | ✅ |
| [SQL](./doc/p/sql.md) | 📝 | .sql | ❌ | ✅ |
| [StarDict](./doc/p/stardict.md) | 📁 | (📝.ifo) | ✅ | ✅ |
| [StarDict Textual File](./doc/p/stardict_textual.md) | 📝 | (.xml) | ✅ | ✅ |
| [Tabfile](./doc/p/tabfile.md) | 📝 | .txt, .tab | ✅ | ✅ |
| [TMX](./doc/p/tmx.md) | 📝 | .tmx | ✅ | |
| [Wiktextract](./doc/p/wiktextract.md) | 📝 | .jsonl | ✅ | ❌ |
| [XDXF](./doc/p/xdxf.md) | 📝 | .xdxf | ✅ | ❌ |
| [XLIFF](./doc/p/xliff.md) | 📝 | .xlf, .xliff | ✅ | |
| [Zim (Kiwix)](./doc/p/zim.md) | 🔢 | .zim | ✅ | ✅ |
| [ABBYY Lingvo DSL](./doc/p/dsl.md) 🇷🇺 | 📝 | .dsl | ✅ | ❌ |
| [Almaany.com](./doc/p/almaany.md) (Arabic) | 🛢️ | .db | ✅ | ❌ |
| [cc-kedict](./doc/p/cc_kedict.md) 🇰🇷 | 📝 | | ✅ | ❌ |
| [Dict.cc](./doc/p/dict_cc.md) 🇩🇪 | 🛢️ | .db | ✅ | |
| [DigitalNK](./doc/p/digitalnk.md) 🇰🇵 | 🛢️ | .db | ✅ | |
| [EDICT2 (CEDICT)](./doc/p/edict2.md) 🇨🇳 | 📝 | (.u8) | ✅ | ❌ |
| [EPWING](./doc/p/epwing.md) 🇯🇵 | 📁 | | ✅ | ❌ |
| [JMDict](./doc/p/jmdict.md) 🇯🇵 | 📝 | | ✅ | ❌ |
| [JMnedict](./doc/p/jmnedict.md) 🇯🇵 | 📝 | | ✅ | ❌ |
| [WordNet](./doc/p/wordnet.md) 🇬🇧 | 📁 | | ✅ | ❌ |
| [WordFrequency.info](./doc/p/wordfrequency.md) 🇬🇧 | 📝 | .wordfrequency | ✅ | ❌ |
| [@wordset dictionary](./doc/p/wordset.md) 🇬🇧 | 📁 | | ✅ | |
| [Yomichan / Yomitan](./doc/p/yomichan.md) 🇯🇵 | 📦 | (.zip) | ✅ | ✅ |

Legend:

- 📁 Directory
- 📝 Text file
- 📦 Package/archive file
- 🛢️ SQLite file
- 🔢 Binary file
- ✅ Supported
- ❌ Will not be supported

**Note**: SQLite-based formats are not detected by their `.db` extension, so you
must select the format yourself, either in the UI or with the `--read-format` flag.
Do not confuse SQLite-based formats with [SQLite mode](#sqlite-mode), which is a
separate feature.

## Requirements

PyGlossary requires **Python 3.12 or higher**. It works on practically all
mainstream operating systems, including *GNU/Linux*, *Windows*, *macOS*,
*FreeBSD*, and other common Unix-based systems.

As the screenshots show, PyGlossary has several user interfaces, which are
different ways to use the program.

- **Gtk3-based interface** uses [PyGI](http://pygobject.readthedocs.io/en/latest/getting_started.html) with Gtk3.
  It is the best option for most Linux users.
  See [doc/gtk3.md](./doc/gtk3.md) for installation instructions on Linux and macOS.

- **Gtk4-based interface** uses [PyGI](http://pygobject.readthedocs.io/en/latest/getting_started.html) with Gtk4.
  See [doc/gtk4.md](./doc/gtk4.md).

- **Qt6-based interface** is a native-looking interface for all operating systems.
  It requires either PySide6 or PyQt6, and uses a wizard-based flow for simplicity.

- **wxPython-based interface** is a wizard-style GUI built with wxPython. Install it with
  `pip install pyglossary[wx]`, or install `wxPython` separately.

- **Tkinter-based interface** is meant for situations where no more modern UI is available.
  It is especially useful on Windows, where Tkinter is installed with Python itself.
  You can [install Tkinter](./doc/tkinter.md) on Linux or macOS.

- **Command-line interface** works on all operating systems without special requirements.
  Run `./main.py --help` or `pyglossary --help` to see its options.

  - **Interactive command-line interface**
    - Requires `prompt_toolkit`: `pip install prompt_toolkit`
    - Well suited to mobile devices, such as Termux on Android, where no GUI is available
    - Selected automatically when no output file argument is passed, and either:
      - On Linux, the `$DISPLAY` environment variable is empty or not set
        (for example, when using a remote Linux machine over SSH)
      - On macOS, no `tkinter` module is found
    - Select it manually with `--cmd` or `--ui=cmd`, for example `./main.py --cmd`
      - You can still pass an input file, or any flag or option
    - If both input and output files are passed, the non-interactive command-line UI is used by default.
      Pass `--interactive` to change this.
    - When writing a script, pass `--no-interactive` to force non-interactive mode.
      You must then pass both input and output file arguments.
    - In prompts, use the *Up/Down* keys to see recently used values,
      and the *Tab* key to see available values and options
    - Press Control+C (on Linux and Windows) at any prompt to exit

## UI (User Interface) selection

When you run PyGlossary without any command-line arguments, flags, or options, it tries each interface in turn and starts the first one it can:

- It looks for PyGI with Gtk3 and opens the **Gtk3-based** interface.
- It looks for PyGI with Gtk4 and opens the **Gtk4-based** interface.
- It looks for PySide6 or PyQt6 and opens the **Qt 6** interface.
- It looks for wxPython and opens the **wxPython-based** interface.
- It looks for Tkinter and opens the **classic Tkinter** interface.
- It opens the **Tk wizard** interface (also Tkinter-based).
- If stdin is connected to a terminal, it looks for `prompt_toolkit` and runs the **interactive command-line** interface.
- Otherwise, it starts an HTTP server and opens the **web interface** in your browser.

The order depends on the operating system. On **GNU/Linux**, the default order is Gtk3, Gtk4, Qt 6, wxPython, Tkinter (classic), Tk wizard, then web. On **macOS** and **Windows**, Qt 6, wxPython, and the Tk wizard are tried before classic Tkinter and Gtk.

To choose a user interface explicitly, use `--ui`:

- `./main.py --ui=gtk3`
- `./main.py --ui=gtk4`
- `./main.py --ui=gtk`, which currently selects `gtk3`
- `./main.py --ui=qt6` or `./main.py --ui=qt`: Qt 6 wizard-based interface
- `./main.py --ui=wx` or `./main.py --wx`: wxPython wizard-based interface
- `./main.py --ui=tk`
- `./main.py --ui=tk_wizard`: wizard-based Tkinter interface
  - Shortcut: `./main.py --tkw`
- `./main.py --ui=web`
- `./main.py --ui=cmd`: interactive command-line interface, when no extra arguments are passed

## Installation on Windows

You can either download the latest `setup.exe` from [Releases](https://github.com/ilius/pyglossary/releases) and install it with the setup wizard, or install PyGlossary with Python and `pip`:

- [Download and install the latest Python](https://www.python.org/downloads/windows/)

- Open Start, type `Command`, right-click Command Prompt, and select Run as administrator

- To make sure `pip` is available, run: `python -m ensurepip --upgrade`

- To install PyGlossary, run: `pip install --upgrade pyglossary`

- You should now be able to run the `pyglossary` command

- If the command is not found, make sure the Python environment variables are set up:

  <img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/screenshots/windows-python39-env-vars.png" width="50%" height="50%"/>

## Installation on macOS (14 & 15)

If you download the DMG file from [Releases](https://github.com/ilius/pyglossary/releases) and install it, macOS may refuse to open the app and show the error **the app is damaged and cannot be opened**. In that case, move the unpacked bundle to `/Applications`, and run one of these commands in Terminal:

```
/usr/bin/xattr -d com.apple.quarantine /Applications/PyGlossaryWX.app
```

Or

```
/usr/bin/xattr -d com.apple.quarantine /Applications/PyGlossaryTK.app
```

Then open the app: right-click the app in Finder, select **Open**, and confirm that you want to run an app not signed by Apple. You only need to do this once.

## Feature-specific requirements

- The [Sort by Locale](#sorting) feature requires [PyICU](./doc/pyicu.md).

- The `--remove-html-all` flag requires `lxml` and `beautifulsoup4`:

  `pip install lxml beautifulsoup4`

Some formats have additional requirements. If you have trouble with a format,
see its documentation via the link in the [supported formats](#supported-formats) table.

The **Qt 6 wizard** GUI (`--ui=qt`, `--ui=qt6`, `--qt`, or `--qt6`) needs PySide6 or PyQt6: `pip install pyglossary[qt6]` (or install `PySide6` separately). On macOS, this extra also installs **`pyobjc-framework-Cocoa`**, so the Dock and app switcher can show the PyGlossary icon. Otherwise, runs started with plain `python` have no app bundle icon.

The **wxPython wizard** GUI (`--ui=wx` or `--wx`) needs wxPython: `pip install pyglossary[wx]` (or install `wxPython` separately). On macOS, this extra also installs **`pyobjc-framework-Cocoa`** for the same Dock icon behavior as the Qt extra.

**Using Termux on Android?** See [doc/termux.md](./doc/termux.md).

## Configuration

See [doc/config.rst](./doc/config.rst).

## Direct and indirect modes

PyGlossary has two ways to convert a glossary:

- **Direct mode** streams entries: each entry is read from the input, processed, and written
  to the output one at a time. This keeps memory usage low. It is the default when the output
  format does not require sorted entries.
- **Indirect mode** reads the whole input before writing the output. Entries are kept in
  memory or, in [SQLite mode](#sqlite-mode), in temporary storage until writing. It is required
  when entries must be sorted before writing (see [Sorting](#sorting)), because sorting needs
  all entries available at once.

Use `--direct` to request direct mode, or `--indirect` to force indirect mode. Direct mode is
not possible when entries must be sorted, so PyGlossary uses indirect mode automatically in
that case and ignores `--direct`.

These output formats always require sorted entries:

- [StarDict](./doc/p/stardict.md)
- [StarDict (Merge Syns)](./doc/p/stardict_merge_syns.md)
- [EPUB-2](./doc/p/epub2.md)
- [EPWING](./doc/p/epwing.md)
- [Yomichan](./doc/p/yomichan.md)
- [DictionaryForMIDs](./doc/p/dicformids.md)

[Mobipocket E-Book](./doc/p/mobi.md) is sorted by default, but you can disable sorting with
`--no-sort` to allow direct mode.

## SQLite mode

When entries must be sorted (see above), PyGlossary needs to hold all of them until sorting
is done. SQLite mode stores them in a temporary SQLite database on disk instead of keeping
them in RAM, so memory usage stays low even for very large glossaries. Depending on your
storage, it may also reduce conversion time.

- SQLite mode is only used when sorting is needed; it has no effect on direct conversions.
- It is enabled automatically when sorting is needed, unless the `auto_sqlite`
  [config parameter](./doc/config.rst) is `false`.
- Pass `--sqlite` to force it on, or `--no-sqlite` to turn it off. With `--no-sqlite`,
  sorting uses an in-memory SQLite database, so all entries still occupy RAM.
- `--sqlite` and `--direct` cannot be used together.
- The temporary database is stored in the [cache directory](#cache-directory) and is deleted
  after conversion, unless you pass `--no-cleanup`.

## Sorting

Entries are sorted before writing when:

- the output format requires it (as explained [above](#direct-and-indirect-modes)), or
- you pass the `--sort` flag.

When sorting, you can also use:

- `--sort-key` to choose the sort key, which determines the sort order (including locale).
  See [doc/sort-key.md](./doc/sort-key.md).

- `--sort-encoding` to change the encoding used for sorting.

  - UTF-8 is the default encoding for all sort keys and output formats, unless stated otherwise.
  - This only affects the order of entries. It does not corrupt words or definitions.
  - Characters that cannot be encoded are replaced with a `?` byte (*only for sorting*).

## Cache directory

The cache directory stores temporary files, which are either moved or deleted
after conversion. Pass `--no-cleanup` to keep them.

The cache directory is located at:

- Linux or BSD: `~/.cache/pyglossary/`
- Mac: `~/Library/Caches/PyGlossary/`
- Windows: `C:\Users\USERNAME\AppData\Local\PyGlossary\Cache\`

## User plugins

To add your own plugin without modifying the source code, or to use a plugin that has
been removed from the repository, place it in this directory:

- Linux or BSD: `~/.pyglossary/plugins/`
- Mac: `~/Library/Preferences/PyGlossary/plugins/`
- Windows: `C:\Users\USERNAME\AppData\Roaming\PyGlossary\plugins\`

## Linux packaging status

[![Packaging status](https://repology.org/badge/vertical-allrepos/pyglossary.svg?columns=3&header=PyGlossary)](https://repology.org/project/pyglossary/versions)

## Using PyGlossary as a library

See [doc/lib/usage.md](./doc/lib/usage.md) for how to use PyGlossary as a Python library.

## Plugin development

To learn how to develop plugins, see the [test plugin](./pyglossary/plugins/testformat/), a basic example, or the [CSV plugin](./pyglossary/plugins/csv_plugin).

Third-party and user plugins should only import the modules listed in the [Third-party plugin API](./doc/plugin-api.md).

Whenever you add a plugin, or change the options or metadata of an existing plugin, run the [`./scripts/gen`](./scripts/gen) script to update the generated files (index and documentation) that the project keeps.

## Internals

See [ARCHITECTURE.md — Entry model and filters](./ARCHITECTURE.md#entry-model-and-filters) for information about internal glossary structure and entry filters.
