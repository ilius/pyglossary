
### General Information ###
Name | Stardict
---- | -------
Description | StarDict (.ifo)
Extensions | `.ifo`
Read support | Yes
Write support | Yes
Single-file | No
Wiki | [StarDict](https://en.wikipedia.org/wiki/StarDict)
Website | http://www.huzheng.org/stardict/


### Read options ###
Name | Default | Type | Comment
---- | ---- | ------- | -------
`unicode_errors` | `strict` | str | What to do with Unicode decoding errors
`xdxf_to_html` | `True` | bool | 

### Write options ###
Name | Default | Type | Comment
---- | ---- | ------- | -------
`audio_goldendict` | `False` | bool | Convert audio links for GoldenDict (desktop)
`audio_icon` | `True` | bool | Add glossary's audio icon
`dictzip` | `True` | bool | Compress .dict file to .dict.dz
`merge_syns` | `False` | bool | Write alternates to .idx instead of .syn
`sametypesequence` |  | str | Definition format: h=html, m=plaintext, x=xdxf
`stardict_client` | `False` | bool | Modify html entries for StarDict 3.0
