"""Regression evidence for PostgreSQL constraints and teaching counterexamples.
These check already implemented behavior, not retroactively claimed RED steps.
"""
from decimal import Decimal as D
import psycopg
import pytest
from test_reports import catalog_db, report_db


def test_parameters_keep_sql_looking_product_name_as_data(catalog_db):
    dangerous = "店長's coffee'); DROP TABLE sku; --"
    with psycopg.connect(catalog_db) as c:
        p = c.execute('INSERT INTO product(name) VALUES (%s) RETURNING id', (dangerous,)).fetchone()[0]
        assert c.execute('SELECT name FROM product WHERE id=%s',(p,)).fetchone() == (dangerous,)
        assert c.execute("SELECT to_regclass('sku')").fetchone() == ('sku',)


@pytest.mark.parametrize('case', ['duplicate','orphan','null_price','null_name','null_code'])
def test_catalog_database_guards(report_db, case):
    with psycopg.connect(report_db) as c:
        p = c.execute("SELECT product_id FROM sku WHERE code='COFFEE-250'").fetchone()[0]
        with pytest.raises(psycopg.IntegrityError):
            with c.transaction():
                if case=='duplicate':
                    c.execute("INSERT INTO sku(code,product_id,price) VALUES ('COFFEE-250',%s,320)",(p,))
                elif case=='orphan':
                    c.execute("INSERT INTO sku(code,product_id,price) VALUES ('ORPHAN',-1,320)")
                elif case=='null_price':
                    c.execute("INSERT INTO sku(code,product_id,price) VALUES ('BAD',%s,NULL)",(p,))
                elif case=='null_name':
                    c.execute('INSERT INTO product(name) VALUES (NULL)')
                else:
                    c.execute('INSERT INTO sku(code,product_id,price) VALUES (NULL,%s,320)',(p,))
        assert c.execute('SELECT count(*) FROM sku').fetchone() == (4,)


def test_referenced_sku_cannot_be_deleted_but_can_be_deactivated(report_db):
    with psycopg.connect(report_db) as c:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            with c.transaction():
                c.execute("DELETE FROM sku WHERE code='COFFEE-250'")
        c.execute("UPDATE sku SET active=false WHERE code='COFFEE-250'")
        assert c.execute("SELECT revenue FROM demo_september_sales WHERE code='COFFEE-250'").fetchone() == (D('1240'),)
        assert c.execute("SELECT active FROM sku WHERE code='COFFEE-250'").fetchone() == (False,)


def test_zero_price_nullable_weight_and_price_update_do_not_rewrite_demo_sales(report_db):
    with psycopg.connect(report_db) as c:
        c.execute("UPDATE sku SET price=0,weight_g=NULL WHERE code='COFFEE-250'")
        assert c.execute("SELECT price,weight_g FROM sku WHERE code='COFFEE-250'").fetchone() == (D('0'),None)
        assert c.execute("SELECT revenue FROM demo_september_sales WHERE code='COFFEE-250'").fetchone() == (D('1240'),)


def test_inner_join_where_filter_and_count_star_are_not_zero_sales_reports(report_db):
    with psycopg.connect(report_db) as c:
        wrong = c.execute("""SELECT s.code FROM sku s LEFT JOIN demo_sale d ON d.sku_code=s.code
            WHERE d.status='shipped' AND d.sold_on >= '2026-09-01' AND d.sold_on < '2026-10-01'
            GROUP BY s.code ORDER BY s.code""").fetchall()
        assert wrong == [('COFFEE-250',),('FILTER-100',)]
        counts=c.execute("""SELECT count(*),count(d.id) FROM sku s
            LEFT JOIN demo_sale d ON d.sku_code=s.code AND d.status='shipped'
            AND d.sold_on >= '2026-09-01' AND d.sold_on < '2026-10-01'
            WHERE s.code='DRIPPER'""").fetchone()
        assert counts==(1,0)
        print('COUNTEREXAMPLE zero-sale COUNT(*),COUNT(d.id):',counts)


def test_join_multiplication_and_sum_distinct_both_give_wrong_totals(report_db):
    with psycopg.connect(report_db) as c:
        multiplied = c.execute("""SELECT sum(d.qty*d.unit_price) FROM demo_sale d
            JOIN demo_tag t ON t.sku_code=d.sku_code
            WHERE d.status='shipped' AND d.sold_on >= '2026-09-01' AND d.sold_on < '2026-10-01'""").fetchone()[0]
        distinct = c.execute("""SELECT sum(DISTINCT d.qty*d.unit_price) FROM demo_sale d
            JOIN demo_tag t ON t.sku_code=d.sku_code WHERE d.sku_code='COFFEE-250'
            AND d.status='shipped' AND d.sold_on >= '2026-09-01' AND d.sold_on < '2026-10-01'""").fetchone()[0]
        correct = c.execute('SELECT sum(revenue) FROM demo_september_sales').fetchone()[0]
        assert (multiplied,distinct,correct)==(D('2840'),D('940'),D('1600'))
        print('COUNTEREXAMPLE multiplied,distinct-coffee,correct-all:',multiplied,distinct,correct)
