# etl/database.py
from sqlalchemy import create_engine
from .config import get_database_url

def setup_database():
    engine = create_engine(get_database_url())
    with engine.connect() as conn:
        conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
        conn.commit()