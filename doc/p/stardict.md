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
| unicode_errors | `strict` | str  | What to do with Unicode decoding errors |

### Write options

| Name             | Default | Type | Comment                                        |
| ---------------- | ------- | ---- | ---------------------------------------------- |
| dictzip          | `True`  | bool | Compress .dict file to .dict.dz                |
| sametypesequence |         | str  | Definition format: h=html, m=plaintext, x=xdxf |
| stardict_client  | `False` | bool | Modify html entries for StarDict 3.0           |
| merge_syns       | `False` | bool | Write alternates to .idx instead of .syn       |
| audio_goldendict | `False` | bool | Convert audio links for GoldenDict (desktop)   |
| audio_icon       | `True`  | bool | Add glossary's audio icon                      |



### Dictionary Applications/Tools

| Name & Website                                                                            | License     | Platforms           |
| ----------------------------------------------------------------------------------------- | ----------- | ------------------- |
| [GoldenDict](http://goldendict.org/)                                                      | GPL         | Linux, Windows      |
| [StarDict](http://huzheng.org/stardict/)                                                  | GPL         | Linux, Windows, Mac |
| [GoldenDict Mobile (Free)](http://goldendict.mobi/)                                       | Freemium    | Android             |
| [GoldenDict Mobile (Full)](http://goldendict.mobi/)                                       | Proprietary | Android             |
| [Twinkle Star Dictionary](https://play.google.com/store/apps/details?id=com.qtier.dict)   | Unknown     | Android             |
| [WordMateX](https://apkcombo.com/wordmatex/org.d1scw0rld.wordmatex/)                      | Proprietary | Android             |
| [QDict](https://play.google.com/store/apps/details?id=com.annie.dictionary)               | Apache 2.0  | Android             |
| [Fora Dictionary](https://play.google.com/store/apps/details?id=com.ngc.fora)             | Freemium    | Android             |
| [Fora Dictionary Pro](https://play.google.com/store/apps/details?id=com.ngc.fora.android) | Proprietary | Android             |
