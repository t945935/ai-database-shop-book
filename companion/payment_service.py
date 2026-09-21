"""Application-level idempotency for simulated payment events."""
from decimal import Decimal
import psycopg


def capture_idempotent(db, event, order_id, amount, status):
    value = Decimal(str(amount))
    if value < 0 or value != value.quantize(Decimal('0.01')):
        raise ValueError('amount must be nonnegative with two decimals')
    if status not in {'authorized', 'captured', 'failed', 'refunded'}:
        raise ValueError('invalid payment status')
    with psycopg.connect(db) as c, c.transaction():
        old = c.execute(
            "SELECT order_id,amount,status FROM payment_event WHERE event=%s FOR UPDATE",
            (event,),
        ).fetchone()
        if old:
            if old != (order_id, value, status):
                raise ValueError('payment payload conflict')
            return {'event': event, 'replayed': True}
        c.execute(
            "INSERT INTO payment_event(event,order_id,amount,status) VALUES (%s,%s,%s,%s)",
            (event, order_id, value, status),
        )
        return {'event': event, 'replayed': False}
