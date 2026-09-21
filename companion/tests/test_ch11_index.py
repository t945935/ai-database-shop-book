from pathlib import Path
import psycopg
from test_catalog import catalog_db


def test_index_exists_and_query_plan_can_use_it(catalog_db):
    with psycopg.connect(catalog_db) as c:
        product=c.execute("INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id").fetchone()[0]
        c.execute("INSERT INTO sku(code,product_id,price) VALUES ('COFFEE-250',%s,320)",(product,))
        c.execute(Path('lessons/ch11_setup.sql').read_text())
        before='\n'.join(row[0] for row in c.execute("EXPLAIN SELECT * FROM demo_sale WHERE sku_code='COFFEE-250' AND sold_on >= DATE '2026-09-01'").fetchall())
        c.execute(Path('lessons/ch11_index.sql').read_text())
        after='\n'.join(row[0] for row in c.execute("EXPLAIN SELECT * FROM demo_sale WHERE sku_code='COFFEE-250' AND sold_on >= DATE '2026-09-01'").fetchall())
        print('PLAN BEFORE:',before)
        print('PLAN AFTER:',after)
        assert c.execute("SELECT indexname FROM pg_indexes WHERE indexname='demo_sale_sku_date_idx'").fetchone() == ('demo_sale_sku_date_idx',)
        c.execute('SET enable_seqscan=off')
        diagnostic='\n'.join(row[0] for row in c.execute("EXPLAIN SELECT * FROM demo_sale WHERE sku_code='COFFEE-250' AND sold_on >= DATE '2026-09-01'").fetchall())
        analyze='\n'.join(row[0] for row in c.execute("EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM demo_sale WHERE sku_code='COFFEE-250' AND sold_on >= DATE '2026-09-01'").fetchall())
        print('PLAN INDEX DIAGNOSTIC:',diagnostic)
        print('PLAN ANALYZE BUFFERS:',analyze)
        assert 'demo_sale_sku_date_idx' in diagnostic
        assert 'Buffers:' in analyze
