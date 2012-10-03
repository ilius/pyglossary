PyGlossary
==========

Working on glossarys (dictionary databases) using python. Including editing glossarys and converting theme between many formats such as: Tabfile StarDict format xFarDic format "Babylon Builder" source format Omnidic format and etc.

Requirements
------------
- BeautifulSoup required to sanitize html contents.
  ``sudo easy_install beautifulsoup``
- Dictionary Development Kit as part of `Auxillary Tools for Xcode <http://developer.apple.com/downloads>`_. Extract to ``/Developer/Extras/Dictionary Development Kit``

HOWTOs
------------
Convert Babylon (bgl) to Mac OS X dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's assume the Babylon dict is at ``~/Documents/Duden_Synonym.BGL``::

    python src/convert_appledict.py ~/Documents/Duden_Synonym.BGL Duden_Synonym
    cd Duden_Synonym
    make
    make install

Launch Dictionary.app and test.
