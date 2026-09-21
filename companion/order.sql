CREATE TABLE sales_order (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_note text,
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','confirmed','cancelled')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE order_item (
    order_id bigint NOT NULL REFERENCES sales_order(id) ON DELETE CASCADE,
    sku_code text NOT NULL REFERENCES sku(code) ON DELETE RESTRICT,
    qty integer NOT NULL CHECK (qty > 0),
    unit_price numeric NOT NULL CHECK (unit_price >= 0 AND unit_price < 10000000000 AND unit_price = round(unit_price, 2)),
    line_total numeric GENERATED ALWAYS AS (qty * unit_price) STORED,
    PRIMARY KEY (order_id, sku_code)
);
