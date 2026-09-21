from decimal import Decimal as D
from pathlib import Path
import psycopg
import pytest
from test_catalog import catalog_db
from purchase_service import receive_idempotent

@pytest.fixture
def purchase_db(catalog_db):
    with psycopg.connect(catalog_db) as c:
        c.execute(Path('purchase.sql').read_text())
        p=c.execute("INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id").fetchone()[0]
        c.execute("INSERT INTO sku(code,product_id,price) VALUES ('COFFEE-250',%s,320)",(p,))
        supplier=c.execute("INSERT INTO supplier(name) VALUES ('山城烘豆商') RETURNING id").fetchone()[0]
        po=c.execute("INSERT INTO purchase_order(supplier_id) VALUES (%s) RETURNING id",(supplier,)).fetchone()[0]
        item=c.execute("INSERT INTO purchase_item(order_id,sku_code,ordered_qty,unit_cost) VALUES (%s,'COFFEE-250',10,100) RETURNING id",(po,)).fetchone()[0]
    return catalog_db,item

def receive(c,item,event,qty):
    row=c.execute("SELECT ordered_qty,coalesce((SELECT sum(qty) FROM receipt_item WHERE purchase_item_id=%s),0) FROM purchase_item WHERE id=%s FOR UPDATE",(item,item)).fetchone()
    if row[1]+qty>row[0]: raise ValueError('over-receipt')
    c.execute("INSERT INTO receipt(event) VALUES (%s)",(event,))
    c.execute("INSERT INTO receipt_item(receipt_event,purchase_item_id,qty) VALUES (%s,%s,%s)",(event,item,qty))

def test_purchase_supports_partial_receipts_and_remaining_quantity(purchase_db):
    db,item=purchase_db
    with psycopg.connect(db) as c:
        receive(c,item,'GRN-1',4); receive(c,item,'GRN-2',3)
        assert c.execute("SELECT ordered_qty-sum(qty) FROM purchase_item pi JOIN receipt_item ri ON ri.purchase_item_id=pi.id WHERE pi.id=%s GROUP BY ordered_qty",(item,)).fetchone()==(3,)

def test_purchase_rejects_over_receipt_without_partial_row(purchase_db):
    db,item=purchase_db
    with psycopg.connect(db) as c:
        receive(c,item,'GRN-1',8)
        with pytest.raises(ValueError,match='over-receipt'):
            receive(c,item,'GRN-2',3)
        assert c.execute('SELECT count(*) FROM receipt_item').fetchone()==(1,)

def test_same_receipt_event_is_unique(purchase_db):
    db,item=purchase_db
    with psycopg.connect(db) as c:
        receive(c,item,'GRN-1',4)
        with pytest.raises(psycopg.errors.UniqueViolation):
            with c.transaction(): c.execute("INSERT INTO receipt(event) VALUES ('GRN-1')")


def test_receive_service_replays_same_payload_and_rejects_conflict(purchase_db):
    db,item=purchase_db
    assert receive_idempotent(db,item,'GRN-SERVICE',4)=={'event':'GRN-SERVICE','qty':4,'replayed':False}
    assert receive_idempotent(db,item,'GRN-SERVICE',4)=={'event':'GRN-SERVICE','qty':4,'replayed':True}
    with pytest.raises(ValueError,match='idempotency payload conflict'):
        receive_idempotent(db,item,'GRN-SERVICE',3)
    with psycopg.connect(db) as c:
        assert c.execute("SELECT count(*) FROM receipt_item WHERE receipt_event='GRN-SERVICE'").fetchone()==(1,)
