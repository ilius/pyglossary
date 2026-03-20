## DICT.org file format (.index)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/dict_org/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                                                        |
| --------------- | ---------------------------------------------------------------------------- |
| Name            | DictOrg                                                                      |
| snake_case_name | dict_org                                                                     |
| Description     | DICT.org file format (.index)                                                |
| Extensions      | `.index`                                                                     |
| Read support    | Yes                                                                          |
| Write support   | Yes                                                                          |
| Single-file     | No                                                                           |
| Kind            | 📁 directory                                                                  |
| Sort-on-write   | No (by default)                                                              |
| Sort key        | (`headword_lower`)                                                           |
| Wiki            | [DICT#DICT file format](https://en.wikipedia.org/wiki/DICT#DICT_file_format) |
| Website         | [The DICT Development Group](http://dict.org/bin/Dict)                       |

### Write options

| Name    | Default | Type | Comment                                 |
| ------- | ------- | ---- | --------------------------------------- |
| dictzip | `False` | bool | Compress .dict file to .dict.dz         |
| install | `True`  | bool | Install dictionary to /usr/share/dictd/ |

### Dictionary Applications/Tools

| Name & Website                                                  | Source code | License | Platforms | Language |
| --------------------------------------------------------------- | ----------- | ------- | --------- | -------- |
| [Dictd](https://directory.fsf.org/wiki/Dictd)                   | ―           | GPL     | Linux     |          |
| [GNOME Dictionary](https://wiki.gnome.org/Apps/Dictionary)      | ―           | GPL     | Linux     |          |
| [Xfce4 Dictionary](https://docs.xfce.org/apps/xfce4-dict/start) | ―           | GPL     | linux     |          |
| [Ding](https://www-user.tu-chemnitz.de/~fri/ding/)              | ―           | GPL     | linux     |          |

### Related Formats

- [DICT.org dictfmt source file](./dict_org_source.md)
- [dictunformat output file](./dictunformat.md)
