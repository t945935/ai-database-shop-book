from pathlib import Path
from decimal import Decimal as D
import psycopg
import pytest
from test_catalog import catalog_db


@pytest.fixture
def report_db(catalog_db):
    with psycopg.connect(catalog_db) as c:
        c.execute(Path('lessons/ch02.sql').read_text())
        for file in ['lessons/ch03_setup.sql','lessons/ch03_report.sql']:
            if Path(file).exists():
                c.execute(Path(file).read_text())
    return catalog_db


def test_september_report_preserves_zero_sales(report_db):
    with psycopg.connect(report_db) as c:
        assert c.execute("SELECT to_regclass('demo_september_sales')").fetchone()[0], 'sales report not implemented'
        rows = c.execute('SELECT code,units,revenue FROM demo_september_sales ORDER BY code').fetchall()
        print('REPORT:',rows)
        assert rows == [('COFFEE-250',4,D('1240')),('COFFEE-500',0,D('0')),('DRIPPER',0,D('0')),('FILTER-100',3,D('360'))]


def test_tag_filter_does_not_multiply_sales(report_db):
    query = Path('lessons/ch03_tag_filter.sql')
    assert query.exists(), 'tag-safe sales filter not implemented'
    with psycopg.connect(report_db) as c:
        assert c.execute(query.read_text()).fetchall() == [('COFFEE-250',4,D('1240'))]
