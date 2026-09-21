-- Chapter 02 catalog; applied to an empty per-test schema.
CREATE TABLE product (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL CHECK (btrim(name) <> '')
);

CREATE TABLE sku (
    code text PRIMARY KEY CHECK (btrim(code) <> '' AND code = btrim(code)),
    product_id bigint NOT NULL REFERENCES product(id) ON DELETE RESTRICT,
    weight_g integer CHECK (weight_g > 0),
    price numeric NOT NULL CHECK (price >= 0 AND price < 10000000000 AND price = round(price, 2)),
    active boolean NOT NULL DEFAULT true
);
