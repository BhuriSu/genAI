import os

from utils.db import DBConnection


def get_warehouse_creds() -> DBConnection:
    return DBConnection(
        user=os.getenv('POSTGRES_USER', 'postgresql'),
        pwd=os.getenv('POSTGRES_PASSWORD', 'testpostgresql'),
        database=os.getenv('POSTGRES_DB', 'postgresql'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
    )