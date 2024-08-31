import os

from utils.db import DBConnection


def get_warehouse_creds() -> DBConnection:
    return DBConnection(
        user=os.getenv('POSTGRES_USER', 'root'),
        pwd=os.getenv('POSTGRES_PASSWORD', 'Testmysql111'),
        database=os.getenv('POSTGRES_DB', 'MySQL80'),
        host=os.getenv('POSTGRES_HOST', '127.0.0.1'),
        port=int(os.getenv('POSTGRES_PORT', 3306)),
    )