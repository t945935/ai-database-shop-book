from decimal import Decimal
from pathlib import Path
import psycopg
import pytest
from integrated_service import checkout, capture_payment, ship_paid


def integrated_db(db):
    with psycopg.connect(db) as c:
        c.execute(Path('integrated_schema.sql').read_text())
        c.execute("INSERT INTO sku(code,name) VALUES ('BEANS-250','Beans')")
        c.execute("INSERT INTO balance(sku,physical,value) VALUES ('BEANS-250',10,100)")
    return db


def test_checkout_payment_and_fulfillment_are_one_connected_flow(db):
    db=integrated_db(db)
    order=checkout(db,'checkout-1','BEANS-250',2,Decimal('12.50'),'demo')
    assert capture_payment(db,'checkout-1','payment-1',Decimal('25.00')) == order
    assert ship_paid(db,'checkout-1','shipment-1','fulfillment-1') == order
    with psycopg.connect(db) as c:
        assert c.execute("SELECT status FROM sales_order WHERE id=%s",(order,)).fetchone()==('shipped',)
        assert c.execute("SELECT physical,reserved FROM balance WHERE sku='BEANS-250'").fetchone()==(8,0)
        assert c.execute("SELECT count(*) FROM ledger").fetchone()==(2,)


def test_checkout_is_idempotent_and_payload_conflict_is_rejected(db):
    db=integrated_db(db)
    first=checkout(db,'checkout-2','BEANS-250',1,Decimal('10.00'))
    assert checkout(db,'checkout-2','BEANS-250',1,Decimal('10.00')) == first
    with pytest.raises(ValueError, match='payload mismatch'):
        checkout(db,'checkout-2','BEANS-250',2,Decimal('10.00'))


def test_unpaid_order_cannot_ship(db):
    db=integrated_db(db)
    checkout(db,'checkout-3','BEANS-250',1,Decimal('10.00'))
    with pytest.raises(ValueError, match='not paid'):
        ship_paid(db,'checkout-3','shipment-3','fulfillment-3')
