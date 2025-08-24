## JMDict (xml)

### General Information

| Attribute       | Value                                                            |
| --------------- | ---------------------------------------------------------------- |
| Name            | JMDict                                                           |
| snake_case_name | jmdict                                                           |
| Description     | JMDict (xml)                                                     |
| Extensions      |                                                                  |
| Read support    | Yes                                                              |
| Write support   | No                                                               |
| Single-file     | Yes                                                              |
| Kind            | 📝 text                                                           |
| Wiki            | [JMdict](https://en.wikipedia.org/wiki/JMdict)                   |
| Website         | [The JMDict Project](https://www.edrdg.org/jmdict/j_jmdict.html) |

### Read options

| Name            | Default | Type | Comment                                |
| --------------- | ------- | ---- | -------------------------------------- |
| example_padding | `10`    | int  | Padding for examples (in px)           |
| example_color   |         | str  | Examples color                         |
| translitation   | `False` | bool | Add translitation (romaji) of keywords |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml), [python-romkan-ng](https://pypi.org/project/python-romkan-ng)

To install, run:

```sh
pip3 install lxml python-romkan-ng
```

### Related Formats

- [EDICT2 (CEDICT) (.u8)](./edict2.md)
- [JMnedict](./jmnedict.md)
