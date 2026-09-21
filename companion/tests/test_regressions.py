"""Supplemental regression checks of already implemented behavior (not RED claims)."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal as D
import psycopg
import pytest
import shop
from test_inventory import row, hold


@pytest.mark.parametrize("qty", [0, -1, 1.5, True])
def test_invalid_quantities(db, qty):
    with pytest.raises(ValueError):
        shop.receive(db,"bad","BEAN",qty,"1")
    assert row(db,"select count(*) from ledger") == (0,)


@pytest.mark.parametrize("cost", ["-1", "NaN", "Infinity", "0.0000001"])
def test_invalid_costs(db, cost):
    with pytest.raises(ValueError):
        shop.receive(db,"bad","BEAN",1,cost)
    assert row(db,"select count(*) from ledger") == (0,)


def test_deplete_in_separate_shipments(db):
    shop.receive(db,"A","BEAN",1,"1")
    shop.receive(db,"B","BEAN",2,"0")
    for i in range(3):
        hold(db,f"O{i}","BEAN",1)
        shop.ship(db,f"S{i}",f"O{i}")
    assert shop.stock(db,"BEAN") == (0,0,0,D(0),D(0))
    assert row(db,"select sum(cost) from shipment") == (D(1),)
    assert shop.reconcile(db) == []


def test_all_event_payload_conflicts(db):
    shop.receive(db,"A","BEAN",4,"100")
    for sku, qty, cost in [("OTHER",4,"100"),("BEAN",3,"100"),("BEAN",4,"101")]:
        with pytest.raises(ValueError,match="idempotency"):
            shop.receive(db,"A",sku,qty,cost)
    hold(db,"O1","BEAN",1)
    hold(db,"O1","BEAN",1)
    with pytest.raises(ValueError,match="idempotency"):
        hold(db,"O1","BEAN",2)
    hold(db,"O2","BEAN",1)
    shop.ship(db,"S1","O1")
    with pytest.raises(ValueError,match="idempotency"):
        shop.ship(db,"S1","O2")
    assert shop.reconcile(db) == []


def test_ledger_failure_rolls_back_balance_and_document(db):
    shop.receive(db,"A","BEAN",4,"100")
    hold(db,"O1","BEAN",1)
    before = shop.stock(db,"BEAN")
    with psycopg.connect(db) as c:
        c.execute("ALTER TABLE ledger ADD CONSTRAINT reject_ship CHECK(kind <> 'ship')")
    with pytest.raises(psycopg.errors.CheckViolation):
        shop.ship(db,"S1","O1")
    assert shop.stock(db,"BEAN") == before
    assert row(db,"select count(*) from shipment") == (0,)
    assert row(db,"select consumed from reservation") == (False,)
    assert shop.reconcile(db) == []


def test_parallel_same_receipt_key(db):
    barrier = Barrier(2)
    def attempt(_):
        barrier.wait(timeout=10)
        shop.receive(db,"A","BEAN",1,"100")
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(attempt,range(2)))
    assert shop.stock(db,"BEAN")[:4] == (1,0,1,D(100))
    assert row(db,"select count(*) from ledger") == (1,)


def test_parallel_returns_cannot_exceed_shipment(db):
    shop.receive(db,"A","BEAN",1,"100")
    hold(db,"O1","BEAN",1)
    shop.ship(db,"S1","O1")
    barrier = Barrier(2)
    def attempt(event):
        barrier.wait(timeout=10)
        try:
            shop.restock(db,event,"S1",1)
            return True
        except ValueError as e:
            assert str(e) == "over-return"
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt,["T1","T2"]))
    assert sum(results) == 1
    assert shop.stock(db,"BEAN")[:4] == (1,0,1,D(100))
    assert shop.reconcile(db) == []


def test_reconcile_reservation_source(db):
    shop.receive(db,"A","BEAN",2,"100")
    hold(db,"O1","BEAN",1)
    with psycopg.connect(db) as c:
        c.execute("UPDATE reservation SET consumed=true")
    assert shop.reconcile(db) == [("BEAN",0,0,D(0),1)]


def test_database_rejects_negative_stock_and_orphan(db):
    shop.receive(db,"A","BEAN",1,"100")
    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(db) as c:
            c.execute("UPDATE balance SET reserved=2")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with psycopg.connect(db) as c:
            c.execute("INSERT INTO reservation(event,sku,qty) VALUES ('O','missing',1)")
    assert shop.reconcile(db) == []
