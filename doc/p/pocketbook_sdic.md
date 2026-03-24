## PocketBook SDIC (.dic)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/pocketbook_sdic/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                  |
| --------------- | ---------------------- |
| Name            | PocketBookSdic         |
| snake_case_name | pocketbook_sdic        |
| Description     | PocketBook SDIC (.dic) |
| Extensions      | `.dic`                 |
| Read support    | No                     |
| Write support   | Yes                    |
| Single-file     | Yes                    |
| Kind            | 🔢 binary               |
| Sort-on-write   | Never                  |
| Sort key        | (`headword_lower`)     |
| Wiki            | ―                      |
| Website         | ―                      |

### Write options

| Name            | Default | Type | Comment                                                                     |
| --------------- | ------- | ---- | --------------------------------------------------------------------------- |
| metadata_dir    |         | str  | Path to a directory containing collates.txt, morphems.txt, and keyboard.txt |
| collates_path   |         | str  | Path to collates.txt (overrides metadata_dir)                               |
| keyboard_path   |         | str  | Path to keyboard.txt (overrides metadata_dir)                               |
| morphems_path   |         | str  | Path to morphems.txt (overrides metadata_dir)                               |
| merge_separator | `<br>`  | str  | Separator for merging duplicate headwords                                   |
