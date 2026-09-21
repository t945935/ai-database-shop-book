from pathlib import Path
from decimal import Decimal as D
import psycopg
import pytest
from test_catalog import catalog_db


def test_ch02_walkthrough(catalog_db):
    script = Path('lessons/ch02.sql')
    assert script.exists(), 'chapter 02 executable walkthrough not implemented'
    with psycopg.connect(catalog_db) as c:
        c.execute(script.read_text())
        assert c.execute('SELECT code,weight_g,price,active FROM sku ORDER BY code').fetchall() == [
            ('COFFEE-250',250,D('350'),True),
            ('COFFEE-500',500,D('600'),False),
            ('DRIPPER',None,D('450'),True),
            ('FILTER-100',None,D('120'),True),
        ]
        print('CATALOG:', c.execute('SELECT code,weight_g,price,active FROM sku ORDER BY code').fetchall())
        assert c.execute('SELECT count(*) FROM product').fetchone() == (3,)
