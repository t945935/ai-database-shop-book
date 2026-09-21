import os
from pathlib import Path
import uuid
import psycopg
from psycopg import sql
import pytest

@pytest.fixture
def db():
    dsn = os.environ["SHOP_DSN"]
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    scoped = psycopg.conninfo.make_conninfo(dsn, options=f"-csearch_path={schema}")
    with psycopg.connect(scoped) as c:
        c.execute(Path("schema.sql").read_text())
    yield scoped
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
