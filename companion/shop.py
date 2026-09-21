"""Single-SKU, TWD inventory. Each call commits or rolls back as one unit."""
from decimal import Decimal, ROUND_HALF_UP
import psycopg
from psycopg.types.json import Jsonb

SCALE = Decimal("0.000001")


def _quantity(qty):
    if type(qty) is not int or qty <= 0:
        raise ValueError("quantity must be a positive integer")


def _lock(c, sku):
    c.execute("INSERT INTO balance(sku) VALUES (%s) ON CONFLICT DO NOTHING", (sku,))
    return c.execute("SELECT physical,reserved,value FROM balance WHERE sku=%s FOR UPDATE", (sku,)).fetchone()


def _replay(c, event, payload):
    # Serialize the key even if competing payloads target different SKUs.
    c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (event,))
    old = c.execute("SELECT payload FROM ledger WHERE event=%s", (event,)).fetchone()
    if old and old[0] != payload:
        raise ValueError("idempotency payload mismatch")
    return bool(old)


def _post(c, event, kind, sku, payload, physical, reserved, value):
    c.execute("UPDATE balance SET physical=physical+%s,reserved=reserved+%s,value=value+%s WHERE sku=%s", (physical,reserved,value,sku))
    c.execute("INSERT INTO ledger(event,kind,sku,payload,physical_delta,reserved_delta,value_delta) VALUES (%s,%s,%s,%s,%s,%s,%s)", (event,kind,sku,Jsonb(payload),physical,reserved,value))


def receive(db, event, sku, qty, unit_cost):
    _quantity(qty)
    if isinstance(unit_cost, float):
        raise ValueError("float cost is not accepted; use Decimal or string")
    cost = Decimal(unit_cost)
    if not cost.is_finite() or cost < 0 or cost != cost.quantize(SCALE):
        raise ValueError("cost must be nonnegative, at most six decimals")
    payload = ["receive", sku, qty, str(cost.quantize(SCALE))]
    with psycopg.connect(db) as c:
        if _replay(c,event,payload):
            return
        _lock(c,sku)
        _post(c,event,"receive",sku,payload,qty,0,cost*qty)


def reserve(c, event, sku, qty):
    """Caller owns connection; transaction context commits if no outer transaction."""
    _quantity(qty)
    payload = ["reserve", sku, qty]
    with c.transaction():
        if _replay(c,event,payload):
            return
        physical, reserved, _ = _lock(c,sku)
        if physical-reserved < qty:
            raise ValueError("insufficient available stock")
        c.execute("INSERT INTO reservation(event,sku,qty) VALUES (%s,%s,%s)", (event,sku,qty))
        _post(c,event,"reserve",sku,payload,0,qty,Decimal(0))


def confirm_and_reserve(c, order_id, event, sku, qty, target_status='confirmed'):
    if target_status != 'confirmed':
        raise ValueError('order must be draft')
    with c.transaction():
        status = c.execute("SELECT status FROM sales_order WHERE id=%s FOR UPDATE", (order_id,)).fetchone()
        if not status or status[0] != 'draft':
            raise ValueError('order must be draft')
        item = c.execute("SELECT qty FROM order_item WHERE order_id=%s AND sku_code=%s", (order_id, sku)).fetchone()
        if not item or item[0] != qty:
            raise ValueError('order item mismatch')
        reserve(c, event, sku, qty)
        c.execute("UPDATE sales_order SET status='confirmed' WHERE id=%s", (order_id,))


def release(db, event, reservation):
    payload = ["release", reservation]
    with psycopg.connect(db) as c:
        if _replay(c,event,payload):
            return
        r = c.execute("SELECT sku,qty,consumed FROM reservation WHERE event=%s FOR UPDATE", (reservation,)).fetchone()
        if not r:
            raise ValueError("unknown reservation")
        sku, qty, consumed = r
        if consumed:
            raise ValueError("reservation already consumed")
        _lock(c,sku)
        c.execute("UPDATE reservation SET consumed=true WHERE event=%s", (reservation,))
        _post(c,event,"release",sku,payload,0,-qty,Decimal(0))


def ship(db, event, reservation):
    payload = ["ship", reservation]
    with psycopg.connect(db) as c:
        if _replay(c,event,payload):
            return
        r = c.execute("SELECT sku,qty,consumed FROM reservation WHERE event=%s FOR UPDATE", (reservation,)).fetchone()
        if not r:
            raise ValueError("unknown reservation")
        sku, qty, consumed = r
        if consumed:
            raise ValueError("reservation already consumed")
        physical, _, value = _lock(c,sku)
        cost = (value*qty/physical).quantize(SCALE, rounding=ROUND_HALF_UP)
        c.execute("INSERT INTO shipment(event,reservation,sku,qty,cost) VALUES (%s,%s,%s,%s,%s)", (event,reservation,sku,qty,cost))
        c.execute("UPDATE reservation SET consumed=true WHERE event=%s", (reservation,))
        _post(c,event,"ship",sku,payload,-qty,-qty,-cost)


def restock(db, event, shipment, qty):
    _quantity(qty)
    payload = ["return", shipment, qty]
    with psycopg.connect(db) as c:
        if _replay(c,event,payload):
            return
        s = c.execute("SELECT sku,qty,cost FROM shipment WHERE event=%s FOR UPDATE", (shipment,)).fetchone()
        if not s:
            raise ValueError("unknown shipment")
        sku, shipped, original_cost = s
        returned, refunded = c.execute("SELECT coalesce(sum(qty),0),coalesce(sum(cost),0) FROM returned WHERE shipment=%s", (shipment,)).fetchone()
        if returned+qty > shipped:
            raise ValueError("over-return")
        _lock(c,sku)
        cost = (original_cost*(returned+qty)/shipped).quantize(SCALE, rounding=ROUND_HALF_UP) - refunded
        c.execute("INSERT INTO returned(event,shipment,qty,cost) VALUES (%s,%s,%s,%s)", (event,shipment,qty,cost))
        _post(c,event,"return",sku,payload,qty,0,cost)


def reconcile(db):
    """Return discrepancies: SKU, physical, reserved, value, reservation-source."""
    with psycopg.connect(db) as c:
        return c.execute("""
          WITH totals AS (
            SELECT sku,sum(physical_delta) p,sum(reserved_delta) r,sum(value_delta) v
            FROM ledger GROUP BY sku
          ), holds AS (
            SELECT sku,sum(qty) q FROM reservation WHERE NOT consumed GROUP BY sku
          ), differences AS (
            SELECT b.sku,b.physical-coalesce(t.p,0) dp,
              b.reserved-coalesce(t.r,0) dr,b.value-coalesce(t.v,0) dv,
              b.reserved-coalesce(h.q,0) dh
            FROM balance b LEFT JOIN totals t USING(sku) LEFT JOIN holds h USING(sku)
          ) SELECT * FROM differences WHERE dp<>0 OR dr<>0 OR dv<>0 OR dh<>0 ORDER BY sku
        """).fetchall()


def stock(db, sku):
    with psycopg.connect(db) as c:
        return c.execute("SELECT physical,reserved,physical-reserved,value,CASE WHEN physical=0 THEN 0 ELSE value/physical END FROM balance WHERE sku=%s", (sku,)).fetchone()

