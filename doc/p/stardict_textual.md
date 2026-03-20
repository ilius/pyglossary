## StarDict Textual File (.xml)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/stardict_textual/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                                                                                    |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Name            | StardictTextual                                                                                                          |
| snake_case_name | stardict_textual                                                                                                         |
| Description     | StarDict Textual File (.xml)                                                                                             |
| Extensions      |                                                                                                                          |
| Read support    | Yes                                                                                                                      |
| Write support   | Yes                                                                                                                      |
| Single-file     | Yes                                                                                                                      |
| Kind            | 📝 text                                                                                                                   |
| Sort-on-write   | No (by default)                                                                                                          |
| Sort key        | `stardict`                                                                                                               |
| Wiki            | ―                                                                                                                        |
| Website         | [TextualDictionaryFileFormat](https://github.com/huzheng001/stardict-3/blob/master/dict/doc/TextualDictionaryFileFormat) |

### Read options

| Name         | Default | Type | Comment                      |
| ------------ | ------- | ---- | ---------------------------- |
| encoding     | `utf-8` | str  | Encoding/charset             |
| xdxf_to_html | `True`  | bool | Convert XDXF entries to HTML |

### Write options

| Name     | Default | Type | Comment          |
| -------- | ------- | ---- | ---------------- |
| encoding | `utf-8` | str  | Encoding/charset |

### Dependencies for reading and writing

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```

### Dictionary Applications/Tools

| Name & Website                                                                               | Source code                                                        | License | Platforms           | Language |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------- | ------------------- | -------- |
| [StarDict-Editor (Tools)](https://github.com/huzheng001/stardict-3/blob/master/tools/README) | [@huzheng001/stardict-3](https://github.com/huzheng001/stardict-3) | GPL     | Linux, Windows, Mac | C        |

### Related Formats

- [StarDict (.ifo)](./stardict.md)
- [StarDict (Merge Syns)](./stardict_merge_syns.md)
