## bgl_numEntries (0x0c)

```
bgl_numEntries does not always matches the number of entries in the
	dictionary, but it's close to it.
the difference is usually +- 1 or 2, in rare cases may be 9, 29 and more
```

## bgl_length (0x43)

```
The length of the substring match in a term.
For example, if your glossary contains the term "Dog" and the substring
	length is 2,
search of the substrings "Do" or "og" will retrieve the term dog.
Use substring length 0 for exact match.
```

## bgl_contractions (0x3b)

```
contains a value like this:
V-0#Verb|V-0.0#|V-0.1#Infinitive|V-0.1.1#|V-1.0#|V-1.1#|V-1.1.1#Present Simple|V-1.1.2#Present Simple (3rd pers. sing.)|V-2.0#|V-2.1#|V-2.1.1#Past Simple|V-3.0#|V-3.1#|V-3.1.1#Present Participle|V-4.0#|V-4.1#|V-4.1.1#Past Participle|V-5.0#|V-5.1#|V-5.1.1#Future|V2-0#|V2-0.0#|V2-0.1#Infinitive|V2-0.1.1#|V2-1.0#|V2-1.1#|V2-1.1.1#Present Simple (1st pers. sing.)|V2-1.1.2#Present Simple (2nd pers. sing. & plural forms)|V2-1.1.3#Present Simple (3rd pers. sing.)|V2-2.0#|V2-2.1#|V2-2.1.1#Past Simple (1st & 3rd pers. sing.)|V2-2.1.2#Past Simple (2nd pers. sing. & plural forms)|V2-3.0#|V2-3.1#|V2-3.1.1#Present Participle|V2-4.0#|V2-4.1#|V2-4.1.1#Past Participle|V2-5.0#|V2-5.1#|V2-5.1.1#Future||N-0#Noun|N-1.0#|N-1.1#|N-1.1.1#Singular|N-2.0#|N-2.1#|N-2.1.1#Plural|N4-1.0#|N4-1.1#|N4-1.1.1#Singular Masc.|N4-1.1.2#Singular Fem.|N4-2.0#|N4-2.1#|N4-2.1.1#Plural Masc.|N4-2.1.2#Plural Fem.||ADJ-0#Adjective|ADJ-1.0#|ADJ-1.1#|ADJ-1.1.1#Adjective|ADJ-1.1.2#Comparative|ADJ-1.1.3#Superlative||
value format: (<contraction> "#" [<value>] "|")+
The value is in second language, that is for Babylon Russian-English.BGL
	the value in russian,
for Babylon English-Spanish.BGL the value is spanish (I guess), etc.
```

## bgl_about: Glossary manual file (0x41)

```
additional information about the dictionary
in .txt format this may be short info like this:

Biology Glossary
Author name: Hafez Divandari
Author email: hafezdivandari@gmail.com
-------------------------------------------
A functional glossary for translating
English biological articles to fluent Farsi
-------------------------------------------
Copyright (c) 2009 All rights reserved.

in .pdf format this may be a quite large document (about 30 pages),
an introduction into the dictionary. It describing structure of an article,
editors, how to use the dictionary.

format <file extension> "\x00" <file contents>
file extension may be: ".txt", ".pdf"
```

## bgl_purchaseLicenseMsg (0x2c)

```
contains a value like this:
In order to view this glossary, you must purchase a license.
<br /><a href="http://www.babylon.com/redirects/purchase.cgi?type=170&trid=BPCWHAR">Click here</a> to purchase.
```

## bgl_licenseExpiredMsg (0x2d)

```
contains a value like this:
Your license for this glossary has expired.
In order to view this glossary, you must have a valid license.
<br><a href="http://www.babylon.com/redirects/purchase.cgi?type=130&trid=BPCBRTBR">Renew</a> your license today.
```

## bgl_purchaseAddress (0x2e)

```
contains a value like this:
http://www.babylon.com/redirects/purchase.cgi?type=169&trid=BPCOT
or
mailto:larousse@babylon.com
```
