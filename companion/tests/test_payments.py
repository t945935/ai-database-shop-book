from pathlib import Path
import psycopg
import pytest
from test_catalog import catalog_db
from payment_service import capture_idempotent

@pytest.fixture
def payment_db(catalog_db):
    with psycopg.connect(catalog_db) as c:
        c.execute(Path('order.sql').read_text())
        c.execute(Path('payment.sql').read_text())
        product=c.execute("INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id").fetchone()[0]
        c.execute("INSERT INTO sku(code,product_id,price) VALUES ('COFFEE-250',%s,320)",(product,))
        order=c.execute("INSERT INTO sales_order DEFAULT VALUES RETURNING id").fetchone()[0]
        c.execute("INSERT INTO order_item(order_id,sku_code,qty,unit_price) VALUES (%s,'COFFEE-250',1,320)",(order,))
    return catalog_db,order


def test_payment_event_is_idempotent_and_statuses_are_separate(payment_db):
    db,order=payment_db
    with psycopg.connect(db) as c:
        c.execute("INSERT INTO payment_event(event,order_id,amount,status) VALUES ('PAY-1',%s,320,'captured')",(order,))
        c.execute("INSERT INTO fulfillment(order_id,status) VALUES (%s,'unfulfilled')",(order,))
        c.execute("UPDATE sales_order SET status='confirmed' WHERE id=%s",(order,))
        with pytest.raises(psycopg.errors.UniqueViolation):
            with c.transaction():
                c.execute("INSERT INTO payment_event(event,order_id,amount,status) VALUES ('PAY-1',%s,320,'captured')",(order,))
        assert c.execute("SELECT status FROM sales_order WHERE id=%s",(order,)).fetchone()==('confirmed',)
        assert c.execute("SELECT status FROM fulfillment WHERE order_id=%s",(order,)).fetchone()==('unfulfilled',)
        assert c.execute("SELECT count(*) FROM payment_event WHERE event='PAY-1'").fetchone()==(1,)




def test_payment_service_replays_same_payload_and_rejects_conflict(payment_db):
    db,order=payment_db
    first=capture_idempotent(db,'PAY-SERVICE',order,'320.00','captured')
    replay=capture_idempotent(db,'PAY-SERVICE',order,'320.00','captured')
    assert first['replayed'] is False
    assert replay['replayed'] is True
    with pytest.raises(ValueError, match='payload conflict'):
        capture_idempotent(db,'PAY-SERVICE',order,'321.00','captured')
    with psycopg.connect(db) as c:
        assert c.execute("SELECT count(*) FROM payment_event WHERE event='PAY-SERVICE'").fetchone()==(1,)


def test_payment_amount_cannot_be_negative(payment_db):
    db,order=payment_db
    with psycopg.connect(db) as c:
        with pytest.raises(psycopg.errors.CheckViolation):
            with c.transaction():
                c.execute("INSERT INTO payment_event(event,order_id,amount,status) VALUES ('PAY-BAD',%s,-1,'captured')",(order,))
