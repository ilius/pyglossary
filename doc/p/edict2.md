## EDICT2 (CEDICT) (.u8)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/edict2/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                          |
| --------------- | ---------------------------------------------- |
| Name            | EDICT2                                         |
| snake_case_name | edict2                                         |
| Description     | EDICT2 (CEDICT) (.u8)                          |
| Extensions      | `.u8`                                          |
| Read support    | Yes                                            |
| Write support   | No                                             |
| Single-file     | Yes                                            |
| Kind            | 📝 text                                         |
| Wiki            | [CEDICT](https://en.wikipedia.org/wiki/CEDICT) |
| Website         | ―                                              |

### Read options

| Name                 | Default | Type | Comment                                                                  |
| -------------------- | ------- | ---- | ------------------------------------------------------------------------ |
| encoding             | `utf-8` | str  | Encoding/charset                                                         |
| traditional_title    | `False` | bool | Use traditional Chinese for entry titles/keys                            |
| colorize_tones       | `True`  | bool | Set to false to disable tones coloring                                   |
| link_references      | `False` | bool | Create links to references to other entries                              |
| summary_alternatives | `False` | bool | Include English definition summaries as alternative terms (old behavior) |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```

### Related Formats

- [JMDict (xml)](./jmdict.md)
- [JMnedict](./jmnedict.md)
