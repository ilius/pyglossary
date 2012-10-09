#!/usr/bin/python
# -*- coding: utf-8 -*-
enable = True
format = 'Arianpur'
description = 'Arianpur OpenDictionary (.xml)'
extentions = ['.xml']
readOptions = []
writeOptions = []

##################################

from xml.etree.ElementTree import XML
import time

phoneticColor = '909090'
partOfSpeechColor = '007000'

#link = lambda text, target: '<A HREF="bword://%s">%s</A>'%(target, text)

def clean(text):
  if isinstance(text, unicode):
    text = text.encode('utf-8')
  text = text.strip()
  if text.startswith('![CDATA['):
    return text[8:-2].strip()
  else:
    return text

##################################

def read(glos, filename):
  print 'Loading XML tree...'
  tm0 = time.time()
  tree = XML(file(filename).read())
  tm1 = time.time()
  print '%d seconds left'%(tm1-tm0)

  glos.data = []

  for entry in tree:
    if entry.tag != 'QueerDick_Entry':
      print 'entry.tag="%s" , len(entry)=%d'%(entry.tag, len(entry))
      continue
    word = ''
    phonetic = ''
    partOfSpeech = ''
    defi = ''
    for el in entry:
      tag = el.tag
      if tag=='Index':
        word = clean(el.text)
      elif tag=='Phonetic':
        defi += '/<FONT COLOR="#%s">%s</FONT>/\n'%(phoneticColor, clean(el.text))
      elif tag=='PartOfSpeech':
        defi += '<FONT COLOR="#%s">%s</FONT>\n'%(partOfSpeechColor, clean(el.text))
      elif tag in ('usSoundStartOffset', 'usSoundEndOffset', 'ukSoundStartOffset', 'ukSoundEndOffset'):
        continue
      elif tag=='Meanings':
        for el2 in el:
          if el2.tag != 'Meaning':
            print 'unexpected tag: %r != "Meaning"'%el2.tag
          for el3 in el2:
            if el3.tag == 'MeaningPart':
              #assert el3[0].tag == 'Num' and el3[1].tag == 'Data'
              defi += '● %s\n'%clean(el3[1].text) ## FIXME
            elif el3.tag == 'Example':
              for el4 in el3:
                defi += '<I>%s</I>\n'%clean(el4.text)
            else:
              print 'unexpected tag: %r not MeaningPart or Example'%el3.tag

    defi = defi.strip()

    if word and defi:
      glos.data.append((word, defi))
    else:
      print '\nword=%s  ,  defi=%s\n'%(word, defi.replace('\n', '\\n'))

  glos.setInfo('descriptin', 'Arianpur English Persian (OpenDictionary-September 2010)\nConverted by PyGlossary')
  return True





