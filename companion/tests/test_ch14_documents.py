from pathlib import Path
import psycopg
from test_catalog import catalog_db


def docs_db(catalog_db):
    with psycopg.connect(catalog_db) as c:
        c.execute(Path('lessons/ch14_documents.sql').read_text())
    return catalog_db


def test_current_document_is_filtered_by_effective_date(catalog_db):
    db=docs_db(catalog_db)
    with psycopg.connect(db) as c:
        rows=c.execute("""
            SELECT d.version,ch.body
            FROM supplier_document d JOIN document_chunk ch ON ch.document_id=d.id
            WHERE d.supplier_name='山城烘豆商'
              AND d.effective_from <= DATE '2026-09-01'
              AND (d.effective_to IS NULL OR d.effective_to > DATE '2026-09-01')
        """).fetchall()
        assert rows == [('v2','瑕疵品須於十四日內提出，並附上批次照片。')]


def test_keyword_search_returns_citable_chunk(catalog_db):
    db=docs_db(catalog_db)
    with psycopg.connect(db) as c:
        row=c.execute("""
            SELECT d.version,ch.chunk_no,ch.body
            FROM supplier_document d JOIN document_chunk ch ON ch.document_id=d.id
            WHERE d.effective_from <= %s
              AND (d.effective_to IS NULL OR d.effective_to > %s)
              AND ch.body ILIKE %s
            ORDER BY d.version DESC,ch.chunk_no
            LIMIT 1
        """,('2026-09-01','2026-09-01','%照片%')).fetchone()
        assert row == ('v2',1,'瑕疵品須於十四日內提出，並附上批次照片。')


def test_expired_document_is_not_current(catalog_db):
    db=docs_db(catalog_db)
    with psycopg.connect(db) as c:
        assert c.execute("""
            SELECT count(*) FROM supplier_document
            WHERE effective_from <= DATE '2026-08-01'
              AND (effective_to IS NULL OR effective_to > DATE '2026-08-01')
              AND version='v1'
        """).fetchone() == (0,)
