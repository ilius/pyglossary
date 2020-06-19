
### Required Python libraries for AppleDict

-	**Reading from AppleDict Binary (.dictionary)**

	`sudo pip3 install lxml`

-	**Writing to AppleDict**

	`sudo pip3 install lxml beautifulsoup4 html5lib`


### Requirements for AppleDict on Mac OS X

If you want to convert glossaries into AppleDict format on Mac OS X,
you also need:

-	GNU make as part of [Command Line Tools for
	Xcode](http://developer.apple.com/downloads).
-	Dictionary Development Kit as part of [Additional Tools for
	Xcode](http://developer.apple.com/downloads). Extract to
	`~/Developer/Extras/Dictionary Development Kit`



### Convert Babylon (bgl) to Mac OS X dictionary

Let's assume the Babylon dict is at
`~/Documents/Duden_Synonym/Duden_Synonym.BGL`:

	cd ~/Documents/Duden_Synonym/
	python3 ~/Software/pyglossary/main.py --write-format=AppleDict Duden_Synonym.BGL Duden_Synonym-apple
	cd Duden_Synonym-apple
	make
	make install

Launch Dictionary.app and test.

### Convert Octopus Mdict to Mac OS X dictionary

Let's assume the MDict dict is at
`~/Documents/Duden-Oxford/Duden-Oxford DEED ver.20110408.mdx`.

Run the following command:

	cd ~/Documents/Duden-Oxford/
	python3 ~/Software/pyglossary/main.py --write-format=AppleDict "Duden-Oxford DEED ver.20110408.mdx" "Duden-Oxford DEED ver.20110408-apple"
	cd "Duden-Oxford DEED ver.20110408-apple"
	make
	make install

Launch Dictionary.app and test.


Let's assume the MDict dict is at `~/Downloads/oald8/oald8.mdx`, along
with the image/audio resources file `oald8.mdd`.

Run the following commands: :

	cd ~/Downloads/oald8/
	python3 ~/Software/pyglossary/main.py --write-format=AppleDict oald8.mdx oald8-apple
	cd oald8-apple

This extracts dictionary into `oald8.xml` and data resources into folder
`OtherResources`. Hyperlinks use relative path. :

	sed -i "" 's:src="/:src=":g' oald8.xml

Convert audio file from SPX format to WAV format. You need package
`speex` from [MacPorts](https://www.macports.org) :

	find OtherResources -name "*.spx" -execdir sh -c 'spx={};speexdec $spx  ${spx%.*}.wav' \;
	sed -i "" 's|sound://\([/_a-zA-Z0-9]*\).spx|\1.wav|g' oald8.xml

But be warned that the decoded WAVE audio can consume \~5 times more disk
space!

Compile and install. :

	make
	make install

Launch Dictionary.app and test.
