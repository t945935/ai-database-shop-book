CREATE TABLE payment_event (
    event text PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES sales_order(id) ON DELETE RESTRICT,
    amount numeric NOT NULL CHECK (amount >= 0 AND amount < 10000000000 AND amount = round(amount,2)),
    status text NOT NULL CHECK (status IN ('authorized','captured','failed','refunded')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE fulfillment (
    order_id bigint PRIMARY KEY REFERENCES sales_order(id) ON DELETE RESTRICT,
    status text NOT NULL CHECK (status IN ('unfulfilled','shipped','cancelled'))
);
