from decimal import Decimal as D
from pathlib import Path
import psycopg
import pytest
from test_catalog import catalog_db


@pytest.fixture
def order_db(catalog_db):
    with psycopg.connect(catalog_db) as c:
        c.execute(Path('order.sql').read_text())
        product = c.execute("INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id").fetchone()[0]
        c.execute("INSERT INTO sku(code,product_id,price) VALUES ('COFFEE-250',%s,320),('FILTER-100',%s,120)", (product,product))
    return catalog_db


def test_order_keeps_price_snapshot_and_calculates_multiline_total(order_db):
    with psycopg.connect(order_db) as c:
        with c.transaction():
            order = c.execute("INSERT INTO sales_order(customer_note) VALUES ('門市自取') RETURNING id").fetchone()[0]
            c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) SELECT %s,'COFFEE-250',2,price FROM sku WHERE code='COFFEE-250'", (order,))
            c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) SELECT %s,'FILTER-100',3,price FROM sku WHERE code='FILTER-100'", (order,))
        c.execute("UPDATE sku SET price=999 WHERE code='COFFEE-250'")
        assert c.execute("SELECT sku_code,qty,unit_price,line_total FROM order_item WHERE order_id=%s ORDER BY sku_code", (order,)).fetchall() == [('COFFEE-250',2,D('320'),D('640')),('FILTER-100',3,D('120'),D('360'))]
        assert c.execute("SELECT sum(line_total) FROM order_item WHERE order_id=%s", (order,)).fetchone() == (D('1000'),)


def test_failed_order_transaction_leaves_no_header_or_items(order_db):
    with psycopg.connect(order_db) as c:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            with c.transaction():
                order = c.execute("INSERT INTO sales_order(customer_note) VALUES ('應整體回滾') RETURNING id").fetchone()[0]
                c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'COFFEE-250',1,320)", (order,))
                c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'NOT-A-SKU',1,1)", (order,))
        assert c.execute("SELECT count(*) FROM sales_order WHERE customer_note='應整體回滾'").fetchone() == (0,)
        assert c.execute("SELECT count(*) FROM order_item").fetchone() == (0,)


def test_order_constraints_reject_zero_qty_negative_price_and_duplicate_line(order_db):
    with psycopg.connect(order_db) as c:
        order = c.execute("INSERT INTO sales_order DEFAULT VALUES RETURNING id").fetchone()[0]
        for qty, price in [(0,'320'),(1,'-1')]:
            with pytest.raises(psycopg.errors.CheckViolation):
                with c.transaction():
                    c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'COFFEE-250',%s,%s)", (order,qty,price))
        c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'COFFEE-250',1,320)", (order,))
        with pytest.raises(psycopg.errors.UniqueViolation):
            with c.transaction():
                c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'COFFEE-250',1,320)", (order,))
