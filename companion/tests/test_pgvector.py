from pathlib import Path
import psycopg


def test_pgvector_extension_and_cosine_query(db):
    with psycopg.connect(db) as c:
        c.execute(Path('vector.sql').read_text())
        a='['+','.join(['1']+['0']*767)+']'
        b='['+','.join(['0','1']+['0']*766)+']'
        c.execute("INSERT INTO product_document_embedding VALUES (1,'beans',%s),(2,'filter',%s)",(a,b))
        row=c.execute("SELECT content FROM product_document_embedding ORDER BY embedding <=> %s::vector LIMIT 1",(a,)).fetchone()
        assert row == ('beans',)
        assert c.execute("SELECT extname FROM pg_extension WHERE extname='vector'").fetchone()==('vector',)
