## Anki deck package (.apkg, .colpkg)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/anki_apkg/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                     |
| --------------- | --------------------------------------------------------- |
| Name            | AnkiApkg                                                  |
| snake_case_name | anki_apkg                                                 |
| Description     | Anki deck package (.apkg, .colpkg)                        |
| Extensions      | `.apkg`, `.colpkg`                                        |
| Read support    | Yes                                                       |
| Write support   | No                                                        |
| Single-file     | Yes                                                       |
| Kind            | 🔢 binary                                                  |
| Wiki            | [exporting.html](https://docs.ankiweb.net/exporting.html) |
| Website         | [ankitects/anki](https://github.com/ankitects/anki)       |

### Read options

| Name         | Default | Type | Comment                                            |
| ------------ | ------- | ---- | -------------------------------------------------- |
| word_field   | `0`     | int  | 0-based index of the note field to use as headword |
| include_tags | `False` | bool | Prepend Anki tags to the definition (HTML)         |
