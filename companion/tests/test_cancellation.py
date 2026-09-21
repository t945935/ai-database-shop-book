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
