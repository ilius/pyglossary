## Internal glossary structure

A glossary contains a number of entries.

Each entry contains:

- Headword (title or main term/phrase for lookup)
- Alternates (some alternative terms/phrases for lookup)
- Definition / article

Headword and alternates together are accessible as a single Python list `entry.l_term`, and `entry.l_term[0]` is the headword.

`entry.defi` is the definition as a Python Unicode `str`. Also `entry.b_defi` is definition in UTF-8 byte array (`bytes`).

`entry.defiFormat` is definition format. If definition is plaintext (not rich text), the value is `m`. And if it's in HTML (containing any HTML tag), then `defiFormat` is `h`. The value `x` is also allowed for XDXF, although XDXF is not widely supported in dictionary applications.

There is another type of entry which is called **Data Entry**, and generally contains an image, audio, css, or any other file that was included in input glossary. For data entries:

- `entry.s_term` is file name (and `l_term` is still a list containing this string),
- `entry.defiFormat` is `b`
- `entry.data` gives the content of file in `bytes`.

## Entry filters

Entry filters are internal objects that modify terms/definition of entries,
or remove entries (in some special cases).

Like several filters in a pipe which connects a `reader` object to a `writer` object
(with both of their classes defined in plugins and instantiated in `Glossary` class).

You can enable/disable some of these filters using config parameters / command like flags, which
are documented in [doc/config.rst](./config.rst).

The full list of entry filters is also documented in [doc/entry-filters.md](./entry-filters.md).
