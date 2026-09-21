CREATE TABLE checkout_event (
    event text PRIMARY KEY,
    payload jsonb NOT NULL,
    order_id bigint
);
CREATE TABLE sku (
    code text PRIMARY KEY,
    name text NOT NULL,
    active boolean NOT NULL DEFAULT true
);
CREATE TABLE sales_order (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    checkout_event text NOT NULL UNIQUE REFERENCES checkout_event(event),
    customer_note text,
    status text NOT NULL CHECK (status IN ('confirmed','paid','shipped','cancelled')),
    total numeric(18,2) NOT NULL CHECK (total >= 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE checkout_event ADD CONSTRAINT checkout_order_fk FOREIGN KEY(order_id) REFERENCES sales_order(id);
CREATE TABLE order_item (
    order_id bigint NOT NULL REFERENCES sales_order(id) ON DELETE CASCADE,
    sku text NOT NULL REFERENCES sku(code),
    qty integer NOT NULL CHECK(qty > 0),
    unit_price numeric(18,2) NOT NULL CHECK(unit_price >= 0),
    PRIMARY KEY(order_id, sku)
);
CREATE TABLE payment_event (
    event text PRIMARY KEY,
    order_id bigint NOT NULL UNIQUE REFERENCES sales_order(id),
    amount numeric(18,2) NOT NULL CHECK(amount >= 0),
    status text NOT NULL CHECK(status IN ('captured','failed'))
);
CREATE TABLE fulfillment (
    event text PRIMARY KEY,
    order_id bigint NOT NULL UNIQUE REFERENCES sales_order(id),
    shipment_event text NOT NULL UNIQUE REFERENCES shipment(event)
);
