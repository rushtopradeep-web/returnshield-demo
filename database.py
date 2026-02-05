import sqlite3

def get_db():
    conn = sqlite3.connect("returnshield.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS sellers(
        id INTEGER PRIMARY KEY,
        email TEXT,
        password TEXT,
        state TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orders(
        seller_id INTEGER,
        order_id TEXT,
        name TEXT,
        pin TEXT,
        state TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS returns(
        seller_id INTEGER,
        order_id TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS global_hash(
        hash TEXT,
        count INTEGER
    )""")

    db.commit()
