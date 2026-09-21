from decimal import Decimal as D
import psycopg
import pytest
import shop


def row(db, query, args=()):
    with psycopg.connect(db) as c:
        return c.execute(query, args).fetchone()


def test_receive_idempotent(db):
    assert callable(getattr(shop, "receive", None)), "receive is not implemented"
    shop.receive(db, "R1", "BEAN", 10, "100.00")
    shop.receive(db, "R1", "BEAN", 10, "100.00")
    assert row(db, "select physical, reserved, value from balance") == (10, 0, D("1000"))
    assert row(db, "select count(*) from ledger") == (1,)
    with pytest.raises(ValueError, match="idempotency"):
        shop.receive(db, "R1", "BEAN", 11, "100.00")


def test_moving_average(db):
    shop.receive(db, "A", "COFFEE-250", 4, "100")
    shop.receive(db, "B", "COFFEE-250", 6, "150")
    assert callable(getattr(shop, "stock", None)), "stock average is not implemented"
    assert shop.stock(db, "COFFEE-250") == (10, 0, 10, D("1300"), D("130"))


def hold(db, event, sku, qty):
    with psycopg.connect(db) as c:
        shop.reserve(c, event, sku, qty)


def test_ship_cost_snapshot(db):
    shop.receive(db, "A", "BEAN", 4, "100")
    shop.receive(db, "B", "BEAN", 6, "150")
    hold(db, "O1", "BEAN", 3)
    assert callable(getattr(shop, "ship", None)), "ship is not implemented"
    shop.ship(db, "S1", "O1")
    shop.ship(db, "S1", "O1")
    assert shop.stock(db, "BEAN") == (7, 0, 7, D("910"), D("130"))
    assert row(db, "select qty,cost from shipment") == (3,D("390"))
    with pytest.raises(ValueError, match="consumed"):
        shop.ship(db, "S2", "O1")
    assert row(db, "select count(*) from shipment") == (1,)


def test_return_original_cost_no_overreturn(db):
    shop.receive(db, "A", "BEAN", 4, "100")
    shop.receive(db, "B", "BEAN", 6, "150")
    hold(db, "O1", "BEAN", 3)
    shop.ship(db, "S1", "O1")
    shop.receive(db, "C", "BEAN", 1, "290")
    assert callable(getattr(shop, "restock", None)), "restock is not implemented"
    shop.restock(db, "T1", "S1", 1)
    shop.restock(db, "T1", "S1", 1)
    state = shop.stock(db, "BEAN")
    assert state[:4] == (9, 0, 9, D("1330"))
    assert abs(state[4] - D("1330")/9) < D("0.0000000001")
    assert row(db, "select value_delta from ledger where event='T1'") == (D("130"),)
    before = row(db, "select count(*) from ledger")
    with pytest.raises(ValueError, match="over-return"):
        shop.restock(db, "T2", "S1", 3)
    assert shop.stock(db, "BEAN") == state
    assert row(db, "select count(*) from ledger") == before
    with pytest.raises(ValueError, match="idempotency"):
        shop.restock(db, "T1", "S1", 2)


def test_cost_rounding_full_depletion_and_returns(db):
    shop.receive(db, "A", "BEAN", 1, "0.000001")
    shop.receive(db, "B", "BEAN", 2, "0")
    hold(db, "O1", "BEAN", 3)
    shop.ship(db, "S1", "O1")
    assert shop.stock(db, "BEAN") == (0,0,0,D("0"),D("0"))
    for i in range(3):
        shop.restock(db, f"T{i}", "S1", 1)
    assert shop.stock(db, "BEAN")[3] == D("0.000001")
    assert row(db, "select sum(cost) from returned") == (D("0.000001"),)


def test_reconciliation_detects_tampering(db):
    shop.receive(db, "A", "BEAN", 4, "100")
    hold(db, "O1", "BEAN", 3)
    shop.ship(db, "S1", "O1")
    shop.restock(db, "T1", "S1", 1)
    assert callable(getattr(shop, "reconcile", None)), "reconcile is not implemented"
    assert shop.reconcile(db) == []
    with psycopg.connect(db) as c:
        c.execute("UPDATE balance SET physical=physical+1,value=value+1")
    assert shop.reconcile(db) == [("BEAN", 1, 0, D("1"), 0)]


def test_float_cost_is_rejected(db):
    with pytest.raises(ValueError, match="float"):
        shop.receive(db, "A", "BEAN", 1, 1.0)


@pytest.mark.parametrize("round_no", range(10))
def test_parallel_reserve_last_item(db, round_no):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    shop.receive(db, "A", "BEAN", 1, "100")
    assert callable(getattr(shop, "reserve", None)), "reserve is not implemented"
    barrier = Barrier(2)
    def attempt(key):
        # Connections exist together before either enters the critical section.
        with psycopg.connect(db) as c:
            pid = c.info.backend_pid
            barrier.wait(timeout=10)
            try:
                shop.reserve(c, key, "BEAN", 1)
                return pid, True
            except ValueError:
                return pid, False
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, ["O1", "O2"]))
    print("CONCURRENT BACKENDS:", outcomes)
    assert len({pid for pid, _ in outcomes}) == 2
    assert sum(ok for _, ok in outcomes) == 1
    assert shop.stock(db, "BEAN")[:3] == (1, 1, 0)
    assert row(db, "select count(*) from reservation") == (1,)


