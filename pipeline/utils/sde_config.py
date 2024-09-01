import os

from utils.db import DBConnection


def get_warehouse_creds() -> DBConnection:
    return DBConnection(
        user=os.getenv('MYSQL_USER', 'root'),
        pwd=os.getenv('MYSQL_PASSWORD', 'Testmysql111'),
        database=os.getenv('MYSQL_DB', 'MySQL80'),
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
    )