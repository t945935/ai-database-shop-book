from pathlib import Path
import psycopg
import pytest
import shop
from test_catalog import catalog_db


@pytest.fixture
def order_inventory_db(catalog_db):
    with psycopg.connect(catalog_db) as c:
        c.execute(Path('order.sql').read_text())
        product=c.execute("INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id").fetchone()[0]
        c.execute("INSERT INTO sku(code,product_id,price) VALUES ('COFFEE-250',%s,320)",(product,))
        c.execute("INSERT INTO balance(sku,physical,value) VALUES ('COFFEE-250',1,100)")
        order=c.execute("INSERT INTO sales_order DEFAULT VALUES RETURNING id").fetchone()[0]
        c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'COFFEE-250',1,320)",(order,))
    return catalog_db,order


def test_confirmed_order_reserves_stock_without_depleting_physical(order_inventory_db):
    db,order=order_inventory_db
    with psycopg.connect(db) as c:
        shop.reserve(c, f'order-{order}', 'COFFEE-250', 1)
        c.execute("UPDATE sales_order SET status='confirmed' WHERE id=%s",(order,))
    assert shop.stock(db,'COFFEE-250')[:3] == (1,1,0)


def test_order_cannot_reserve_more_than_available(order_inventory_db):
    db,order=order_inventory_db
    with psycopg.connect(db) as c:
        shop.reserve(c, f'order-{order}', 'COFFEE-250', 1)
    with psycopg.connect(db) as c:
        with pytest.raises(ValueError, match='insufficient'):
            shop.reserve(c, 'order-other', 'COFFEE-250', 1)
    assert shop.stock(db,'COFFEE-250')[:3] == (1,1,0)
