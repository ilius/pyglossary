## EDICT2 (CEDICT) (.u8)

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

| Name              | Default | Type | Comment                                       |
| ----------------- | ------- | ---- | --------------------------------------------- |
| encoding          | `utf-8` | str  | Encoding/charset                              |
| traditional_title | `False` | bool | Use traditional Chinese for entry titles/keys |
| colorize_tones    | `True`  | bool | Set to false to disable tones coloring        |

### Dependencies for reading

PyPI Links: [lxml](https://pypi.org/project/lxml)

To install, run:

```sh
pip3 install lxml
```

### Related Formats

- [JMDict (xml)](./jmdict.md)
- [JMnedict](./jmnedict.md)
