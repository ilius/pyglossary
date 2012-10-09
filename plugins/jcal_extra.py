#!/usr/bin/python
# -*- coding: utf-8 -*-
enable = False
format = 'JcalExtra'
description = 'JCalendar Extra Days'
extentions = ['.xml']
readOptions = []
writeOptions = []

def read(glos, filename, zeroFill=True):
  glos.data=[]
  xml = fa_edit(file(filename).read())
  words=0
  n = len(xml)
  print n
  i=0
  while 0<=i<n:
      i2 = xml.find('<day>', i+1)
      if i2==-1:
        break
      i3 = xml.find('<num>', i2+1)
      i4 = xml.find('</num>', i3+1)
      i5 = xml.find('<desc>', i4+1)
      i6 = xml.find('</desc>', i5+1)
      i = xml.find('</day>', i6+1)
      num = xml[i3+5:i4].strip()
      desc = xml[i5+6:i6].strip()
      if zeroFill:
        p = num.split('/')
        if len(p)==2:
          num='%.2d/%.2d'%(int(p[0]), int(p[1]))
        elif len(p)==3:
          num='%.2d/%.2d/%.2d'%(int(p[0]), int(p[1]), int(p[2]))
        else:
          print 'Invalid date %s'%p
          continue
      glos.data.append([num, desc])
  print('%s words found.'%len(glos.data))
  return True

def write(glos, filename):
  year = glos.getInfo('year')
  if year=='':
    year='1387'
  xml='<?xml version="1.0" encoding="UTF-8"?>\n<cal%s>\n'%year
  for x in glos.data:
    xml += ('<day><num>%s</num><desc>\n%s\n</desc></day>\n'%(x[0],x[1]))
  xml += '</cal%s>'%year
  file(filename, 'w').write(xml)
  return True


def fa_edit(st):
  st = st.replace('ي', 'ی').replace('ك', 'ک')
  for c in (')','،','.',':'):
    st = st.replace(' '+c, c).replace(c, c+' ')
  st = st.replace('( ', '(').replace(' (', '(')
  st = st.replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
  return st
