import psycopg


def receive_idempotent(db, purchase_item_id, event, qty):
    if type(qty) is not int or qty <= 0:
        raise ValueError('qty must be a positive integer')
    with psycopg.connect(db) as c:
        with c.transaction():
            previous=c.execute("""
                SELECT ri.purchase_item_id,ri.qty
                FROM receipt r JOIN receipt_item ri ON ri.receipt_event=r.event
                WHERE r.event=%s
                FOR UPDATE
            """,(event,)).fetchone()
            if previous:
                if previous != (purchase_item_id,qty):
                    raise ValueError('idempotency payload conflict')
                return {'event':event,'qty':qty,'replayed':True}
            ordered=c.execute("SELECT ordered_qty FROM purchase_item WHERE id=%s FOR UPDATE",(purchase_item_id,)).fetchone()[0]
            received=c.execute("SELECT coalesce(sum(qty),0) FROM receipt_item WHERE purchase_item_id=%s",(purchase_item_id,)).fetchone()[0]
            if received+qty>ordered:
                raise ValueError('over-receipt')
            c.execute("INSERT INTO receipt(event) VALUES (%s)",(event,))
            c.execute("INSERT INTO receipt_item(receipt_event,purchase_item_id,qty) VALUES (%s,%s,%s)",(event,purchase_item_id,qty))
            return {'event':event,'qty':qty,'replayed':False}
