import psycopg
import pytest
import shop
from test_inventory import hold


def test_cancel_unshipped_reservation_releases_reserved_stock(db):
    shop.receive(db,'R1','BEAN',2,'100')
    hold(db,'O1','BEAN',1)
    assert callable(getattr(shop,'release',None)), 'release is not implemented'
    shop.release(db,'C1','O1')
    assert shop.stock(db,'BEAN')[:3] == (2,0,2)
    shop.release(db,'C1','O1')
    assert shop.stock(db,'BEAN')[:3] == (2,0,2)
    with psycopg.connect(db) as c:
        with pytest.raises(ValueError, match='consumed'):
            shop.release(db,'C2','O1')


def test_return_uses_original_shipment_cost_and_rejects_overreturn(db):
    shop.receive(db,'R1','BEAN',4,'100')
    from test_inventory import hold
    hold(db,'O1','BEAN',3)
    shop.ship(db,'S1','O1')
    shop.restock(db,'T1','S1',1)
    shop.restock(db,'T1','S1',1)
    assert shop.stock(db,'BEAN')[:4] == (2,0,2,pytest.approx(200))
    with pytest.raises(ValueError, match='over-return'):
        shop.restock(db,'T2','S1',3)
