CREATE TABLE demo_sale (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku_code text NOT NULL REFERENCES sku(code),
    sold_on date NOT NULL,
    qty integer NOT NULL CHECK (qty > 0),
    unit_price numeric NOT NULL CHECK (unit_price >= 0)
);
INSERT INTO demo_sale(sku_code,sold_on,qty,unit_price)
SELECT 'COFFEE-250', DATE '2026-01-01' + (g % 365), 1, 320
FROM generate_series(1,5000) g;
