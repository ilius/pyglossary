PyGlossary
==========

Working on glossarys (dictionary databases) using python. Including editing glossarys and converting theme between many formats. The support matrix is, 
+----------------------------+--------------+------+-------+
| Format                     |   Extension  | Read | Write |
+============================+==============+======+=======+
| ABBYY Lingvo DSL           |     .dsl     |  X   |       |
+----------------------------+--------------+------+-------+
| AppleDict Source           |     .xml     |      |   X   |
+----------------------------+--------------+------+-------+
| Arianpur OpenDictionary    |     .xml     |  X   |       |
+----------------------------+--------------+------+-------+
| Babylon                    |     .bgl     |  X   |       |
+----------------------------+--------------+------+-------+
| Babylon Source             |     .gls     |      |   X   |
+----------------------------+--------------+------+-------+
| DictionaryForMIDs          |              |      |   X   |
+----------------------------+--------------+------+-------+
| DICTD dictionary server    |     .index   |  X   |   X   |
+----------------------------+--------------+------+-------+
| FreeDict                   |     .tei     |      |   X   |
+----------------------------+--------------+------+-------+
| Gettext Source             |     .po      |  X   |   X   |
+----------------------------+--------------+------+-------+
| SQLite                     |  MDic .m2    |  X   |   X   |
|                            |  Sib .sdb    |      |       |
+----------------------------+--------------+------+-------+
| Octopus MDic               |     .mdx     |  X   |       |
+----------------------------+--------------+------+-------+
| Octopus MDic Source        |     .txt     |  X   |   X   |
+----------------------------+--------------+------+-------+
| Omnidic                    |              |  X   |   X   |
+----------------------------+--------------+------+-------+
| PMD                        |              |  X   |   X   |
+----------------------------+--------------+------+-------+
| Sdictionary Binary         |     .dct     |  X   |       |
+----------------------------+--------------+------+-------+
| Sdictionary Source         |     .sdct    |      |   X   |
+----------------------------+--------------+------+-------+
| SQL                        |              |      |   X   |
+----------------------------+--------------+------+-------+
| StarDict                   |     .ifo     |  X   |   X   |
+----------------------------+--------------+------+-------+
| Tabfile                    |  .txt, .dic  |  X   |   X   |
+----------------------------+--------------+------+-------+
| TreeDict                   |              |      |   X   |
+----------------------------+--------------+------+-------+
| XDXF                       |              |  X   |       |
+----------------------------+--------------+------+-------+
| xFarDic                    |     .xdb     |  X   |   X   |
+----------------------------+--------------+------+-------+

Requirements
------------
Mac OS X
~~~~~~~~
- BeautifulSoup4 required to sanitize html contents.

  ``sudo easy_install beautifulsoup4``

- GNU make as part of `Command Line Tools for Xcode  <http://developer.apple.com/downloads>`_.
- Dictionary Development Kit as part of `Auxillary Tools for Xcode <http://developer.apple.com/downloads>`_. Extract to ``/Developer/Extras/Dictionary Development Kit``

HOWTOs
------------
Convert Babylon (bgl) to Mac OS X dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's assume the Babylon dict is at ``~/Documents/Duden_Synonym/Duden_Synonym.BGL``::

    cd ~/Documents/Duden_Synonym/
    ~/Software/pyglossary/pyglossary.pyw --read-options=resPath=OtherResources Duden_Synonym.BGL Duden_Synonym.xml
    make
    make install

Launch Dictionary.app and test.

Convert Octopus Mdict to Mac OS X dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's assume the MDict dict is at ``~/Documents/Duden-Oxford/Duden-Oxford DEED ver.20110408.mdx``.

- Use `GetDict <http://ishare.iask.sina.com.cn/f/23046946.html>`_  to extract Mdict dictionary (.mdx). Choose "UTF-8 TXT" output format and ``Duden-Oxford DEED ver.20110408.mtxt`` output file name. 
- Run the following command::
  
    cd ~/Documents/Duden-Oxford/
    ~/Software/pyglossary/pyglossary.pyw "Duden-Oxford DEED ver.20110408.mtxt" "Duden-Oxford DEED ver.20110408.xml"
    make
    make install

Launch Dictionary.app and test.

Convert Octopus Mdict to Mac OS X dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's assume the MDict dict is at ``~/Downloads/oald8/oald8.mdx``, along with the image/audio resources file ``oald8.mdd``.

Run the following commands: ::

  cd ~/Downloads/oald8/
  ~/Software/pyglossary/pyglossary.pyw --read-options=resPath=OtherResources oald8.mdx oald8.xml

This extracts dictionary into ``oald8.xml`` and data resources into folder ``OtherResources``.
Hyperlinks use relative path. ::

  sed -i "" 's:src="/:src=":g' oald8.xml

Convert audio file from SPX format to WAV format. ::

  find OtherResources -name "*.spx" -execdir sh -c 'spx={};speexdec $spx  ${spx%.*}.wav' \;
  sed -i "" 's|sound://\([/_a-zA-Z0-9]*\).spx|\1.wav|g' oald8.xml

Compile and install. ::
  
  make
  make install

Launch Dictionary.app and test.

