
from sqlalchemy import *
from elixir import *


class Entry(Entity):
    has_field('s_id', Integer)
    has_field('wname', Unicode)
    has_field('wmean', Unicode)


setup_all()


objectstore = SessionContext()


def writeSqlite_ex(glos, filename=''):
    metadata = MetaData()
    metadata.bind = 'sqlite:///' + filename
    metadata.create_all()
    d = glos.data
    n = len(d)
    for i in range(n):
        Entry(s_id=i+1, wname=d[i][0], wmean=d[i][1])
    objectstore.flush()
    # objectstore.clear()
