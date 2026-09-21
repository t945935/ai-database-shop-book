"""Literal SQL snapshots from chapter 03; regenerate after prose edits.
Source equality is checked by the editorial validation, independently of pytest.
"""
from decimal import Decimal
import psycopg
import pytest
from test_reports import catalog_db, report_db

CASES = [('active-expensive', 'SELECT code,price\nFROM sku\nWHERE active AND price >= 300\nORDER BY price DESC,code;', [('DRIPPER', Decimal('450')), ('COFFEE-250', Decimal('350'))]), ('missing-weight', 'SELECT code\nFROM sku\nWHERE weight_g IS NULL\nORDER BY code;', [('DRIPPER',), ('FILTER-100',)]), ('inner-join-misses-zero', "SELECT s.code,sum(d.qty) AS units,sum(d.qty*d.unit_price) AS revenue\nFROM sku s JOIN demo_sale d ON d.sku_code=s.code\nWHERE d.status='shipped'\n  AND d.sold_on >= DATE '2026-09-01'\n  AND d.sold_on < DATE '2026-10-01'\nGROUP BY s.code\nORDER BY s.code;", [('COFFEE-250', 4, Decimal('1240')), ('FILTER-100', 3, Decimal('360'))]), ('count-zero', "SELECT count(*) AS joined_rows,count(d.id) AS matched_sales\nFROM sku s\nLEFT JOIN demo_sale d\n  ON d.sku_code=s.code AND d.status='shipped'\n AND d.sold_on >= DATE '2026-09-01'\n AND d.sold_on < DATE '2026-10-01'\nWHERE s.code='DRIPPER';", [(1, 0)]), ('complete-report', 'SELECT code,units,revenue\nFROM demo_september_sales\nORDER BY code;', [('COFFEE-250', 4, Decimal('1240')), ('COFFEE-500', 0, Decimal('0')), ('DRIPPER', 0, Decimal('0')), ('FILTER-100', 3, Decimal('360'))]), ('positive-report', 'SELECT code,units,revenue\nFROM demo_september_sales\nWHERE units > 0\nORDER BY revenue DESC,code;', [('COFFEE-250', 4, Decimal('1240')), ('FILTER-100', 3, Decimal('360'))]), ('multiplied-sales', "SELECT sum(d.qty*d.unit_price) AS wrong_total\nFROM demo_sale d\nJOIN demo_tag t ON t.sku_code=d.sku_code\nWHERE d.status='shipped'\n  AND d.sold_on >= DATE '2026-09-01'\n  AND d.sold_on < DATE '2026-10-01';", [(Decimal('2840'),)]), ('distinct-is-not-deduplication', "SELECT sum(DISTINCT d.qty*d.unit_price) AS wrong_coffee_total\nFROM demo_sale d\nJOIN demo_tag t ON t.sku_code=d.sku_code\nWHERE d.sku_code='COFFEE-250' AND d.status='shipped'\n  AND d.sold_on >= DATE '2026-09-01'\n  AND d.sold_on < DATE '2026-10-01';", [(Decimal('940'),)])]

@pytest.mark.parametrize('name,query,expected',CASES,ids=[c[0] for c in CASES])
def test_printed_ch03_query(report_db,name,query,expected):
    with psycopg.connect(report_db) as c:
        result = c.execute(query).fetchall()
        print('PRINTED QUERY:',name,result)
        assert result == expected
