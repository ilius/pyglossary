## QuickDic version 6 (.quickdic)

### General Information

| Attribute       | Value                                                                          |
| --------------- | ------------------------------------------------------------------------------ |
| Name            | QuickDic6                                                                      |
| snake_case_name | quickdic6                                                                      |
| Description     | QuickDic version 6 (.quickdic)                                                 |
| Extensions      | `.quickdic`, `.quickdic.v006.zip`                                              |
| Read support    | Yes                                                                            |
| Write support   | Yes                                                                            |
| Single-file     | No                                                                             |
| Kind            | 🔢 binary                                                                       |
| Sort-on-write   | never                                                                          |
| Sort key        | (`headword_lower`)                                                             |
| Wiki            | ―                                                                              |
| Website         | [github.com/rdoeffinger/Dictionary](https://github.com/rdoeffinger/Dictionary) |

### Write options

| Name             | Default | Type | Comment                                            |
| ---------------- | ------- | ---- | -------------------------------------------------- |
| normalizer_rules |         | str  | ICU normalizer rules to use for index sorting      |
| source_lang      |         | str  | The language of the tokens in the dictionary index |
| target_lang      |         | str  | The language of the dictionary entries             |

### Dependencies for reading

PyPI Links: [PyICU](https://pypi.org/project/PyICU)

To install, run:

```sh
pip3 install PyICU
```

### Dictionary Applications/Tools

| Name & Website                                                                           | Source code                                                              | License            | Platforms | Language |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------ | --------- | -------- |
| [Dictionary](https://play.google.com/store/apps/details?id=de.reimardoeffinger.quickdic) | [@rdoeffinger/Dictionary](https://github.com/rdoeffinger/Dictionary)     | Apache License 2.0 | Android   | Java     |
| [DictionaryPC](https://github.com/rdoeffinger/DictionaryPC)                              | [@rdoeffinger/DictionaryPC](https://github.com/rdoeffinger/DictionaryPC) | Apache License 2.0 | Windows   | Java     |
