## Wiktextract (.jsonl)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/wiktextract/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                                |
| --------------- | -------------------------------------------------------------------- |
| Name            | Wiktextract                                                          |
| snake_case_name | wiktextract                                                          |
| Description     | Wiktextract (.jsonl)                                                 |
| Extensions      | `.jsonl`                                                             |
| Read support    | Yes                                                                  |
| Write support   | No                                                                   |
| Single-file     | Yes                                                                  |
| Kind            | 📝 text                                                               |
| Wiki            | ―                                                                    |
| Website         | [@tatuylonen/wiktextract](https://github.com/tatuylonen/wiktextract) |

### Read options

| Name            | Default          | Type | Comment                                        |
| --------------- | ---------------- | ---- | ---------------------------------------------- |
| word_title      | `False`          | bool | Add headwords title to beginning of definition |
| gram_color      | `green`          | str  | Grammar color                                  |
| example_padding | `10px 20px`      | str  | Padding for examples (css value)               |
| audio           | `True`           | bool | Enable audio                                   |
| audio_formats   | `['ogg', 'mp3']` | list | List of audio formats to use                   |
| categories      | `False`          | bool | Enable categories                              |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```
