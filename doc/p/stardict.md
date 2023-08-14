## StarDict (.ifo)

### General Information

| Attribute       | Value                                                |
| --------------- | ---------------------------------------------------- |
| Name            | Stardict                                             |
| snake_case_name | stardict                                             |
| Description     | StarDict (.ifo)                                      |
| Extensions      | `.ifo`                                               |
| Read support    | Yes                                                  |
| Write support   | Yes                                                  |
| Single-file     | No                                                   |
| Kind            | 📁 directory                                          |
| Sort-on-write   | always                                               |
| Sort key        | `stardict`                                           |
| Wiki            | [StarDict](https://en.wikipedia.org/wiki/StarDict)   |
| Website         | [huzheng.org/stardict](http://huzheng.org/stardict/) |

### Read options

| Name           | Default  | Type | Comment                                 |
| -------------- | -------- | ---- | --------------------------------------- |
| xdxf_to_html   | `True`   | bool | Convert XDXF entries to HTML            |
| xsl            | `False`  | bool | Use XSL transformation                  |
| unicode_errors | `strict` | str  | What to do with Unicode decoding errors |

### Write options

| Name             | Default | Type | Comment                                         |
| ---------------- | ------- | ---- | ----------------------------------------------- |
| large_file       | `False` | bool | Use idxoffsetbits=64 bits, for large files only |
| dictzip          | `True`  | bool | Compress .dict file to .dict.dz                 |
| sametypesequence |         | str  | Definition format: h=html, m=plaintext, x=xdxf  |
| stardict_client  | `False` | bool | Modify html entries for StarDict 3.0            |
| merge_syns       | `False` | bool | Write alternates to .idx instead of .syn        |
| audio_goldendict | `False` | bool | Convert audio links for GoldenDict (desktop)    |
| audio_icon       | `True`  | bool | Add glossary's audio icon                       |
| sqlite           | `False` | bool | Use SQLite to limit memory usage                |

### Dictionary Applications/Tools

| Name & Website                                                                            | Source code                                                              | License     | Platforms                                                   | Language |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ----------- | ----------------------------------------------------------- | -------- |
| [AyanDict](https://github.com/ilius/ayandict)                                             | [@ilius/ayandict](https://github.com/ilius/ayandict)                     | GPL         | Linux, Windows, Mac                                         | Go       |
| [The Next Generation GoldenDict](https://github.com/xiaoyifang/goldendict-ng)             | [@xiaoyifang/goldendict-ng](https://github.com/xiaoyifang/goldendict-ng) | GPL         | Linux, Windows, Mac                                         | C++      |
| [GoldenDict](http://goldendict.org/)                                                      | [@goldendict/goldendict](https://github.com/goldendict/goldendict)       | GPL         | Linux, Windows, Mac                                         | C++      |
| [StarDict](http://huzheng.org/stardict/)                                                  | [@huzheng001/stardict-3](https://github.com/huzheng001/stardict-3)       | GPL         | Linux, Windows, Mac                                         | C++      |
| [QStarDict](https://github.com/a-rodin/qstardict)                                         | [@a-rodin/qstardict](https://github.com/a-rodin/qstardict)               | GPLv2       | Linux, Windows, Mac                                         | C++      |
| [GoldenDict Mobile (Free)](http://goldendict.mobi/)                                       | ―                                                                        | Freemium    | Android                                                     |          |
| [GoldenDict Mobile (Full)](http://goldendict.mobi/)                                       | ―                                                                        | Proprietary | Android                                                     |          |
| [Twinkle Star Dictionary](https://play.google.com/store/apps/details?id=com.qtier.dict)   | ―                                                                        | Unknown     | Android                                                     |          |
| [WordMateX](https://apkcombo.com/wordmatex/org.d1scw0rld.wordmatex/)                      | ―                                                                        | Proprietary | Android                                                     |          |
| [QDict](https://play.google.com/store/apps/details?id=com.annie.dictionary)               | [@namndev/QDict](https://github.com/namndev/QDict)                       | Apache 2.0  | Android                                                     | Java     |
| [Fora Dictionary](https://play.google.com/store/apps/details?id=com.ngc.fora)             | ―                                                                        | Freemium    | Android                                                     |          |
| [Fora Dictionary Pro](https://play.google.com/store/apps/details?id=com.ngc.fora.android) | ―                                                                        | Proprietary | Android                                                     |          |
| [KOReader](http://koreader.rocks/)                                                        | [@koreader/koreader](https://github.com/koreader/koreader)               | AGPLv3      | Android, Amazon Kindle, Kobo eReader, PocketBook, Cervantes | Lua      |
| [sdcv](https://dushistov.github.io/sdcv/)                                                 | [@Dushistov/sdcv](https://github.com/Dushistov/sdcv)                     | GPLv2       | Linux, Windows, Mac, Android                                | C++      |
