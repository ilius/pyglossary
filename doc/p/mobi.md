## Mobipocket (.mobi) E-Book

### General Information

| Attribute       | Value                                                  |
| --------------- | ------------------------------------------------------ |
| Name            | Mobi                                                   |
| snake_case_name | mobi                                                   |
| Description     | Mobipocket (.mobi) E-Book                              |
| Extensions      | `.mobi`                                                |
| Read support    | No                                                     |
| Write support   | Yes                                                    |
| Single-file     | No                                                     |
| Kind            | 📦 package                                              |
| Sort-on-write   | default_yes                                            |
| Sort key        | `ebook`                                                |
| Wiki            | [Mobipocket](https://en.wikipedia.org/wiki/Mobipocket) |
| Website         | ―                                                      |

### Write options

| Name                   | Default  | Type | Comment                                                        |
| ---------------------- | -------- | ---- | -------------------------------------------------------------- |
| keep                   | `False`  | bool | Keep temp files                                                |
| group_by_prefix_length | `2`      | int  | Prefix length for grouping                                     |
| css                    |          | str  | Path to css file                                               |
| cover_path             |          | str  | Path to cover file                                             |
| kindlegen_path         |          | str  | Path to kindlegen executable                                   |
| file_size_approx       | `271360` | int  | Approximate size of each xhtml file (example: 200kb)           |
| hide_word_index        | `False`  | bool | Hide headword in tap-to-check interface                        |
| spellcheck             | `True`   | bool | Enable wildcard search and spell correction during word lookup |
| exact                  | `False`  | bool | Exact-match Parameter                                          |

### Other Requirements

Install [KindleGen](https://wiki.mobileread.com/wiki/KindleGen) for creating Mobipocket e-books.

### Dictionary Applications/Tools

| Name & Website                                                             | Source code | License     | Platforms           | Language |
| -------------------------------------------------------------------------- | ----------- | ----------- | ------------------- | -------- |
| [Amazon Kindle](https://www.amazon.com/kindle)                             | ―           | Proprietary | Amazon Kindle       |          |
| [calibre](https://calibre-ebook.com/)                                      | ―           | GPL         | Linux, Windows, Mac |          |
| [Okular](https://okular.kde.org/)                                          | ―           | GPL         | Linux, Windows, Mac |          |
| [Book Reader](https://f-droid.org/en/packages/com.github.axet.bookreader/) | ―           | GPL         | Android             |          |
