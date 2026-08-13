import pg8000.dbapi
from flask import g
import config


def get_conn():
    if "db" not in g:
        g.db = pg8000.dbapi.connect(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=int(config.DB_PORT),
            database=config.DB_NAME,
        )
        g.db.autocommit = True
    return g.db


def close_db(_e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _as_dict(cursor, row):
    if row is None:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def query(sql, params=None, fetch="all"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    if fetch == "one":
        result = _as_dict(cur, cur.fetchone())
    elif fetch == "all":
        rows = cur.fetchall()
        result = [_as_dict(cur, r) for r in rows]
    else:
        result = None
    cur.close()
    return result
