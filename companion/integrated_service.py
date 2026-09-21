"""One-transaction checkout, payment, and fulfillment teaching service."""
from decimal import Decimal
import psycopg
from psycopg.types.json import Jsonb


def _replay(c, event, payload):
    old = c.execute("SELECT payload,order_id FROM checkout_event WHERE event=%s FOR UPDATE", (event,)).fetchone()
    if old:
        if old[0] != payload:
            raise ValueError("checkout idempotency payload mismatch")
        return old[1]
    return None


def checkout(db, event, sku, qty, unit_price, customer_note=None):
    if type(qty) is not int or qty <= 0:
        raise ValueError("quantity must be a positive integer")
    price = Decimal(str(unit_price))
    if price < 0 or price != price.quantize(Decimal("0.01")):
        raise ValueError("unit_price must be nonnegative with two decimals")
    payload = {"sku": sku, "qty": qty, "unit_price": str(price), "customer_note": customer_note}
    with psycopg.connect(db) as c, c.transaction():
        replay = _replay(c, event, payload)
        if replay is not None:
            return replay
        item = c.execute("SELECT active FROM sku WHERE code=%s", (sku,)).fetchone()
        if not item or not item[0]:
            raise ValueError("unknown or inactive SKU")
        physical, reserved, _ = c.execute(
            "SELECT physical,reserved,value FROM balance WHERE sku=%s FOR UPDATE", (sku,)
        ).fetchone()
        if physical - reserved < qty:
            raise ValueError("insufficient available stock")
        total = price * qty
        c.execute("INSERT INTO checkout_event(event,payload) VALUES (%s,%s)", (event, Jsonb(payload)))
        order_id = c.execute(
            "INSERT INTO sales_order(checkout_event,customer_note,status,total) VALUES (%s,%s,'confirmed',%s) RETURNING id",
            (event, customer_note, total),
        ).fetchone()[0]
        c.execute("UPDATE checkout_event SET order_id=%s WHERE event=%s", (order_id, event))
        c.execute("INSERT INTO order_item(order_id,sku,qty,unit_price) VALUES (%s,%s,%s,%s)", (order_id, sku, qty, price))
        reservation = f"checkout:{event}"
        c.execute("INSERT INTO reservation(event,sku,qty) VALUES (%s,%s,%s)", (reservation, sku, qty))
        c.execute("UPDATE balance SET reserved=reserved+%s WHERE sku=%s", (qty, sku))
        c.execute("INSERT INTO ledger(event,kind,sku,payload,physical_delta,reserved_delta,value_delta) VALUES (%s,'reserve',%s,%s,0,%s,0)", (reservation, sku, Jsonb(["reserve", sku, qty]), qty))
        return order_id


def capture_payment(db, event, payment_event, amount):
    value = Decimal(str(amount))
    with psycopg.connect(db) as c, c.transaction():
        order_id, total, status = c.execute("SELECT id,total,status FROM sales_order WHERE checkout_event=%s FOR UPDATE", (event,)).fetchone()
        if status not in ("confirmed", "paid") or value != total:
            raise ValueError("payment amount or order state mismatch")
        old = c.execute("SELECT order_id,amount,status FROM payment_event WHERE event=%s", (payment_event,)).fetchone()
        if old:
            if old != (order_id, value, "captured"):
                raise ValueError("payment idempotency payload mismatch")
            return order_id
        c.execute("INSERT INTO payment_event(event,order_id,amount,status) VALUES (%s,%s,%s,'captured')", (payment_event, order_id, value))
        c.execute("UPDATE sales_order SET status='paid' WHERE id=%s", (order_id,))
        return order_id


def ship_paid(db, event, shipment_event, fulfillment_event):
    with psycopg.connect(db) as c, c.transaction():
        order_id, sku, qty, status = c.execute("SELECT o.id,i.sku,i.qty,o.status FROM sales_order o JOIN order_item i ON i.order_id=o.id WHERE o.checkout_event=%s FOR UPDATE", (event,)).fetchone()
        if status != "paid":
            raise ValueError("order is not paid")
        if c.execute("SELECT 1 FROM fulfillment WHERE event=%s", (fulfillment_event,)).fetchone():
            return order_id
        physical, reserved, value = c.execute("SELECT physical,reserved,value FROM balance WHERE sku=%s FOR UPDATE", (sku,)).fetchone()
        cost = (value * qty / physical).quantize(Decimal("0.000001"))
        reservation = f"checkout:{event}"
        c.execute("INSERT INTO shipment(event,reservation,sku,qty,cost) VALUES (%s,%s,%s,%s,%s)", (shipment_event, reservation, sku, qty, cost))
        c.execute("UPDATE reservation SET consumed=true WHERE event=%s", (reservation,))
        c.execute("UPDATE balance SET physical=physical-%s,reserved=reserved-%s,value=value-%s WHERE sku=%s", (qty, qty, cost, sku))
        c.execute("INSERT INTO ledger(event,kind,sku,payload,physical_delta,reserved_delta,value_delta) VALUES (%s,'ship',%s,%s,%s,%s,%s)", (shipment_event, sku, Jsonb(["ship", reservation]), -qty, -qty, -cost))
        c.execute("INSERT INTO fulfillment(event,order_id,shipment_event) VALUES (%s,%s,%s)", (fulfillment_event, order_id, shipment_event))
        c.execute("UPDATE sales_order SET status='shipped' WHERE id=%s", (order_id,))
        return order_id
