## AppleDict Binary

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/appledict_bin/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------- |
| Name            | AppleDictBin                                                                                  |
| snake_case_name | appledict_bin                                                                                 |
| Description     | AppleDict Binary                                                                              |
| Extensions      | `.dictionary`, `.data`                                                                        |
| Read support    | Yes                                                                                           |
| Write support   | No                                                                                            |
| Single-file     | Yes                                                                                           |
| Kind            | 🔢 binary                                                                                      |
| Wiki            | ―                                                                                             |
| Website         | [Dictionary User Guide for Mac](https://support.apple.com/en-gu/guide/dictionary/welcome/mac) |

### Read options

| Name      | Default | Type | Comment                                             |
| --------- | ------- | ---- | --------------------------------------------------- |
| html      | `True`  | bool | Entries are HTML                                    |
| html_full | `True`  | bool | Turn every entry's definition into an HTML document |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml), [biplist](https://pypi.org/project/biplist)

To install, run:

```sh
pip3 install lxml biplist
```

### Dictionary Applications/Tools

| Name & Website                                                                   | Source code | License     | Platforms | Language |
| -------------------------------------------------------------------------------- | ----------- | ----------- | --------- | -------- |
| [Apple Dictionary](https://support.apple.com/en-gu/guide/dictionary/welcome/mac) | ―           | Proprietary | Mac       |          |

### Related Formats

- [AppleDict Source](./appledict.md)
