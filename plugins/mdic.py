#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Mdic'
description = 'SQLite(MDic m2, Sib sdb)'
extentions = ('.m2', '.sdb')
readOptions = ()
writeOptions = ()

infoKeys = ('dbname', 'author', 'version', 'direction', 'origLang', 'destLang',
            'license', 'category', 'description')

def read(glos, filename):
  from sqlite3 import connect

  ## ???????? name OR dbname ????????????????????
  glos.data=[]
  con = connect(filename)
  cur = con.cursor()
  for key in infoKeys:
    try:
      cur.execute('select %s from dbinfo'%key)
    except:
      pass
    else:
      value = cur.fetchone()[0].encode('utf8')
      if value!='':
        glos.setInfo(key, value)
  cur.execute('select * from word')
  for x in cur.fetchall():
    try:
      w = x[1].encode('utf8')
      m = x[2].encode('utf8')
    except:
      printAsError('error while encoding word %s'%x[0])
    else:
      glos.data.append([w,m])
  cur.close()
  con.close()
  return True

def read_2(glos, filename):
  import alchemy
  return alchemy.readSqlite(glos, filename)

def write(glos, filename):
  lines = glos.getSqlLines()
  fp = open(filename, 'wb')
  fp.write('\n'.join(lines))
  fp.close()
  return True

def write_ext(glos, filename):
  ## This method uses binary module "_mdicbuilder"
  ## but this binary module is deleted from package PyGlossary, and not used by GUI now.
  ## If you want to use it, compile it yourglos, or get it from an older version of PyGlossary (version 2008.08.30)
  import _mdicbuilder
  from _mdicbuilder import MDicBuilder_addHeadword
  if os.path.exists(filename):
    os.remove(filename)
  db = _mdicbuilder.new_MDicBuilder(filename)
  _mdicbuilder.MDicBuilder_swigregister(db)
  n = len(glos.data)
  ui = glos.ui
  if ui==None:
    for i in xrange(n):
      MDicBuilder_addHeadword(db,
                              glos.data[i][0],
                              glos.data[i][1].replace('\n', '<BR>'),
                              '')
  else:
    ui.progressStart()
    k = 1000
    for i in xrange(n):
      MDicBuilder_addHeadword(db,
                              glos.data[i][0],
                              glos.data[i][1].replace('\n', '<BR>'),
                              '')
      if i%k==0:
        rat = float(i)/n
        ui.progress(rat)
    #ui.progress(1.0, 'Converting Completed')
    ui.progressEnd()
  _mdicbuilder.MDicBuilder_setTitle(db, glos.getInfo('name'))
  _mdicbuilder.MDicBuilder_setAuthor(db, glos.getInfo('author'))
  _mdicbuilder.MDicBuilder_setLicense(db, glos.getInfo('license'))
  _mdicbuilder.MDicBuilder_setOrigLang(db, g.getInfo('origLang'))
  _mdicbuilder.MDicBuilder_setDestLang(db, g.getInfo('destLang'))
  _mdicbuilder.MDicBuilder_setDescription(db, glos.getInfo('description'))
  _mdicbuilder.MDicBuilder_setComments(db, g.getInfo('comments'))
  _mdicbuilder.MDicBuilder_setEmail(db, g.getInfo('email'))
  _mdicbuilder.MDicBuilder_setWebsite(db, g.getInfo('website'))
  _mdicbuilder.MDicBuilder_setVersion(db, g.getInfo('version'))
  _mdicbuilder.MDicBuilder_setcreationTime(db, '')
  _mdicbuilder.MDicBuilder_setLastUpdate(db, '')
  _mdicbuilder.MDicBuilder_finish(db)



def write_2(glos, filename):
  import alchemy
  alchemy.writeSqlite(glos, filename)

def write_3(glos, filename):
  import exir
  exir.writeSqlite_ex(glos, filename)
  return True

def writeMdic(glos, filename):
  from sqlite3 import connect
  if os.path.exists(filename):
    os.remove(filename)
  con = connect(filename)
  cur = con.cursor()
  sqlLines = glos.getSqlLines(info=[(key, glos.getInfo(key)) for key in infoKeys], newline='<BR>')
  n = len(sqlLines)
  ui = glos.ui
  if ui==None:
    for i in xrange(n):
      try:
        cur.execute(sqlLines[i])
      except:
        myRaise(__file__)
        printAsError('Error while executing: '+sqlLines[i])
        continue
  else:
    ui.progressStart()
    k = 1000
    for i in xrange(n):
      try:
        con.execute(sqlLines[i])
      except:
        myRaise(__file__)
        printAsError('Error while executing: '+sqlLines[i])
        continue
      if i%k==0:
        rat = float(i)/n
        ui.progress(rat)
    ui.progressEnd()
  cur.close()
  con.close()
  return True

