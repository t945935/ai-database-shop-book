from pathlib import Path
from decimal import Decimal as D
import psycopg
import pytest


@pytest.fixture
def catalog_db(db):
    schema = Path('catalog.sql')
    if schema.exists():
        with psycopg.connect(db) as c:
            c.execute(schema.read_text())
    return db


def test_product_has_independent_variants(catalog_db):
    with psycopg.connect(catalog_db) as c:
        assert c.execute("SELECT to_regclass('product'), to_regclass('sku')").fetchone() == ('product', 'sku'), 'catalog tables not implemented'
        product = c.execute("INSERT INTO product(name) VALUES (%s) RETURNING id", ('日常配方豆',)).fetchone()[0]
        for code, weight, price in [('COFFEE-250',250,'320'),('COFFEE-500',500,'600')]:
            c.execute('INSERT INTO sku(code,product_id,weight_g,price) VALUES (%s,%s,%s,%s)', (code,product,weight,price))
        assert c.execute('SELECT code,weight_g,price,active FROM sku ORDER BY code').fetchall() == [('COFFEE-250',250,D('320'),True),('COFFEE-500',500,D('600'),True)]
        assert c.execute('SELECT count(*) FROM product').fetchone() == (1,)


@pytest.mark.parametrize('price', ['-1', '0.001', 'NaN', 'Infinity', '10000000000'])
def test_price_rejects_invalid_values(catalog_db, price):
    with psycopg.connect(catalog_db) as c:
        p = c.execute("INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id").fetchone()[0]
        with pytest.raises(psycopg.errors.CheckViolation):
            with c.transaction():
                c.execute('INSERT INTO sku(code,product_id,price) VALUES (%s,%s,%s)', ('BAD',p,price))
        assert c.execute('SELECT count(*) FROM sku').fetchone() == (0,)


@pytest.mark.parametrize('field,value', [('name',' '),('code',' '),('weight_g',0),('weight_g',-1)])
def test_catalog_rejects_empty_identity_or_nonpositive_weight(catalog_db, field, value):
    with psycopg.connect(catalog_db) as c:
        p = c.execute("INSERT INTO product(name) VALUES ('測試商品') RETURNING id").fetchone()[0]
        with pytest.raises(psycopg.errors.CheckViolation):
            with c.transaction():
                if field == 'name':
                    c.execute('INSERT INTO product(name) VALUES (%s)', (value,))
                elif field == 'code':
                    c.execute('INSERT INTO sku(code,product_id,price) VALUES (%s,%s,10)', (value,p))
                else:
                    c.execute("INSERT INTO sku(code,product_id,price,weight_g) VALUES ('BAD',%s,10,%s)", (p,value))
