import sqlite3
import ctypes
import json
import os
import os.path

from .exc import DAPIError

def get_hash_for_db(value):
    return ctypes.c_int(value).value

def get_hash_from_db(value):
    return ctypes.c_uint(value).value

def load_manifest(db_path, name):
    if not os.path.exists(db_path):
        raise DAPIError('Database does not exist at "%s"' % db_path)

    results = {}

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.execute('SELECT name FROM sqlite_master WHERE type = "table"')
        table_names = map(lambda ent: ent[0], cur.fetchall())

        if name not in table_names:
            raise DAPIError('Unable to find table "%s"' % name)

        entries = {}

        for row in conn.execute('SELECT id, json FROM %s' % name):
            id = ctypes.c_uint(row[0]).value
            value = json.loads(row[1])
            entries[id] = value

        return entries
    except sqlite3.OperationalError, ex:
        raise DAPIError('Error running database query: %s' % str(ex))
    except Exception, ex:
        raise DAPIError('General error querying database: %s' % str(ex))
