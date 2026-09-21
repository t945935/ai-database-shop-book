import os
from pathlib import Path
import subprocess
import tempfile
import uuid

import psycopg
from psycopg import sql
import pytest


def schema_name(db):
    with psycopg.connect(db) as c:
        return c.execute("SELECT current_schema()").fetchone()[0]


def test_readonly_role_can_select_but_cannot_write(db):
    schema=schema_name(db)
    role='report_'+uuid.uuid4().hex[:12]
    with psycopg.connect(db) as admin:
        admin.execute("CREATE TABLE security_demo(id integer PRIMARY KEY, note text)")
        admin.execute("INSERT INTO security_demo VALUES (1,'fixture')")
        admin.commit()
        admin.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role)))
        admin.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(schema),sql.Identifier(role)))
        admin.execute(sql.SQL("GRANT SELECT ON security_demo TO {}").format(sql.Identifier(role)))
        admin.commit()
    try:
        readonly=psycopg.conninfo.make_conninfo(db,user=role)
        with psycopg.connect(readonly) as c:
            assert c.execute("SELECT note FROM security_demo").fetchone()==('fixture',)
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute("INSERT INTO security_demo VALUES (2,'blocked')")
    finally:
        with psycopg.connect(db,autocommit=True) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {} ").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_failed_migration_rolls_back_schema_and_version(db):
    with psycopg.connect(db) as c:
        c.execute("CREATE TABLE schema_version(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
        c.execute("CREATE TABLE migration_demo(id integer PRIMARY KEY)")
    with pytest.raises(psycopg.errors.UniqueViolation):
        with psycopg.connect(db) as c:
            with c.transaction():
                c.execute("ALTER TABLE migration_demo ADD COLUMN note text")
                c.execute("INSERT INTO schema_version(version) VALUES (1)")
                c.execute("INSERT INTO schema_version(version) VALUES (1)")
    with psycopg.connect(db) as c:
        cols=c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='migration_demo' AND column_name='note'").fetchall()
        assert cols==[]
        assert c.execute("SELECT count(*) FROM schema_version").fetchone()==(0,)


def test_dump_and_restore_preserves_fixture(db):
    pg=Path(os.environ['PG_BIN'])
    schema=schema_name(db)
    restore_db='restore_'+uuid.uuid4().hex[:12]
    with psycopg.connect(db) as c:
        c.execute("CREATE TABLE restore_demo(id integer PRIMARY KEY, note text)")
        c.execute("INSERT INTO restore_demo VALUES (1,'backup-fixture')")
    cinfo=psycopg.conninfo.conninfo_to_dict(db)
    cinfo.pop('options',None)
    base_dsn=psycopg.conninfo.make_conninfo(**cinfo)
    with tempfile.TemporaryDirectory(prefix='shop-dump-') as tmp:
        dump=Path(tmp)/'shop.dump'
        subprocess.run([pg/'pg_dump','--format=custom','--file',dump,'--schema',schema,base_dsn],check=True)
        with psycopg.connect(base_dsn,autocommit=True) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restore_db)))
        try:
            restore_dsn=psycopg.conninfo.make_conninfo(**{**cinfo,'dbname':restore_db})
            subprocess.run([pg/'pg_restore','--exit-on-error','--dbname',restore_dsn,dump],check=True)
            with psycopg.connect(restore_dsn) as restored:
                assert restored.execute("SELECT note FROM "+schema+".restore_demo").fetchone()==('backup-fixture',)
        finally:
            with psycopg.connect(base_dsn,autocommit=True) as admin:
                admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(restore_db)))
