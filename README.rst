PyGlossary
==========

Working on glossarys (dictionary databases) using python. Including editing glossarys and converting theme between many formats such as: Tabfile StarDict format xFarDic format "Babylon Builder" source format Omnidic format and etc.

Requirements
------------
Mac OS X
~~~~~~~~
- BeautifulSoup required to sanitize html contents.

  ``sudo easy_install beautifulsoup``

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

Convert Octopus Mdict to Mac OS X dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's assume the MDict dict is at ``~/Documents/Duden-Oxford/Duden-Oxford DEED ver.20110408.mdx``.

- Use `GetDict <http://ishare.iask.sina.com.cn/f/23046946.html>`_  to extract Mdict dictionary (.mdx). Choose "UTF-8 TXT" output format and ``Duden-Oxford DEED ver.20110408.mtxt`` output file name. 
- Run the following command::
  
    cd ~/Documents/Duden-Oxford/
    ~/Software/pyglossary/pyglossary.sh "Duden-Oxford DEED ver.20110408.mtxt" "Duden-Oxford DEED ver.20110408.xml"
    make
    make install

Launch Dictionary.app and test.
