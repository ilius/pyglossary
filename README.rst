PyGlossary
==========

Working on glossarys (dictionary databases) using python. Including editing glossarys and converting theme between many formats such as: Tabfile StarDict format xFarDic format "Babylon Builder" source format Omnidic format and etc.

Requirements
------------
- BeautifulSoup required to sanitize html contents.

  ``sudo easy_install beautifulsoup``

Mac OS X
~~~~~~~~
- GNU make as part of `Command Line Tools for Xcode  <http://developer.apple.com/downloads>`_.
- Dictionary Development Kit as part of `Auxillary Tools for Xcode <http://developer.apple.com/downloads>`_. Extract to ``/Developer/Extras/Dictionary Development Kit``

HOWTOs
------------
Convert Babylon (bgl) to Mac OS X dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's assume the Babylon dict is at ``~/Documents/Duden_Synonym/Duden_Synonym.BGL``::

    cd ~/Documents/Duden_Synonym/
    ~/Software/pyglossary/pyglossary.sh --read-options=resPath=OtherResources Duden_Synonym.BGL Duden_Synonym.xml
    make
    make install

Launch Dictionary.app and test.
