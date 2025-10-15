# backend/db.py
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("dbname")

def _conn():
    return psycopg2.connect(
        user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, dbname=DB_NAME
    )

@contextmanager
def get_conn():
    conn = _conn()
    try:
        yield conn
    finally:
        conn.close()
