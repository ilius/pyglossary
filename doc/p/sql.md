## SQL (.sql)

<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/sql/__init__.py file, then run ./scripts/gen
-->

### General Information

| Attribute       | Value                                    |
| --------------- | ---------------------------------------- |
| Name            | Sql                                      |
| snake_case_name | sql                                      |
| Description     | SQL (.sql)                               |
| Extensions      | `.sql`                                   |
| Read support    | No                                       |
| Write support   | Yes                                      |
| Single-file     | Yes                                      |
| Kind            | 📝 text                                   |
| Sort-on-write   | No (by default)                          |
| Sort key        | (`headword_lower`)                       |
| Wiki            | [SQL](https://en.wikipedia.org/wiki/SQL) |
| Website         | ―                                        |

### Write options

| Name           | Default | Type | Comment                      |
| -------------- | ------- | ---- | ---------------------------- |
| encoding       | `utf-8` | str  | Encoding/charset             |
| info_keys      | `None`  | list | List of dbinfo table columns |
| add_extra_info | `True`  | bool | Create dbinfo_extra table    |
| newline        | `<br>`  | str  | Newline string               |
| transaction    | `False` | bool | Use TRANSACTION              |
