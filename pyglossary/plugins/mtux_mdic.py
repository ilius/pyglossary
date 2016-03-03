# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'MtuxMdic'
description = 'SQLite(MDic m2, Sib sdb)'
extentions = ['.m2', '.sdb']
readOptions = []
writeOptions = []

infoKeys = [
    'dbname',
    'author',
    'version',
    'direction',
    'origLang',
    'destLang',
    'license',
    'category',
    'description',
]

def read(glos, filename):
    from sqlite3 import connect

    ## ???????? name OR dbname ????????????????????
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
            log.error('error while encoding word %s'%x[0])
        else:
            glos.addEntry(w, m)
    cur.close()
    con.close()
    return True

def read_2(glos, filename):
    import pyglossary.alchemy as alchemy
    return alchemy.readSqlite(glos, filename)


def write_2(glos, filename):
    import pyglossary.alchemy as alchemy
    alchemy.writeSqlite(glos, filename)

def write_3(glos, filename):
    import pyglossary.exir as exir
    exir.writeSqlite_ex(glos, filename)
    return True

def write(glos, filename):
    from sqlite3 import connect
    if os.path.exists(filename):
        os.remove(filename)
    con = connect(filename)
    cur = con.cursor()
    for line in glos.iterSqlLines(
        infoKeys=infoKeys,
        newline='<BR>',
        transaction=False,
    ):
        try:
            cur.execute(line)
        except:
            log.exception('error executing sqlite query:')
            log.error('Error while executing: '+line)
            continue
    
    cur.close()
    con.close()
    return True

