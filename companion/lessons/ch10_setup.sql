-- Chapter 10 standalone teaching fixtures.
-- These are operational facts, not a payment or production order integration.
CREATE TABLE ch10_sku (
    code text PRIMARY KEY,
    name text NOT NULL CHECK (btrim(name) <> '')
);

CREATE TABLE ch10_shipment (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku_code text NOT NULL REFERENCES ch10_sku(code),
    shipped_on date NOT NULL,
    qty integer NOT NULL CHECK (qty > 0),
    unit_cost_snapshot numeric(12,2) NOT NULL CHECK (unit_cost_snapshot >= 0)
);

CREATE TABLE ch10_sale (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_id bigint NOT NULL UNIQUE REFERENCES ch10_shipment(id),
    sku_code text NOT NULL REFERENCES ch10_sku(code),
    sold_on date NOT NULL,
    status text NOT NULL CHECK (status IN ('shipped','cancelled')),
    qty integer NOT NULL CHECK (qty > 0),
    unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE ch10_refund (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sale_id bigint NOT NULL REFERENCES ch10_sale(id),
    refunded_on date NOT NULL,
    qty integer NOT NULL CHECK (qty > 0),
    refund_amount numeric(12,2) NOT NULL CHECK (refund_amount >= 0)
);

INSERT INTO ch10_sku(code,name) VALUES
('BEANS-250','配方豆 250g'),
('EMPTY-100','零銷售練習品'),
('FILTER-100','濾紙 100 入');

INSERT INTO ch10_shipment(sku_code,shipped_on,qty,unit_cost_snapshot) VALUES
('BEANS-250','2026-09-01',2,100),
('BEANS-250','2026-09-15',2,120),
('FILTER-100','2026-09-05',2,40),
('BEANS-250','2026-09-30',1,120),
('BEANS-250','2026-10-01',1,120);

INSERT INTO ch10_sale(shipment_id,sku_code,sold_on,status,qty,unit_price)
SELECT id,sku_code,shipped_on,'shipped',qty,
       CASE sku_code
           WHEN 'BEANS-250' THEN CASE shipped_on
               WHEN DATE '2026-09-01' THEN 350
               WHEN DATE '2026-09-15' THEN 380
               WHEN DATE '2026-09-30' THEN 390
               ELSE 370 END
           ELSE 120
       END
FROM ch10_shipment;

INSERT INTO ch10_refund(sale_id,refunded_on,qty,refund_amount)
SELECT id,DATE '2026-09-20',1,300
FROM ch10_sale
WHERE sku_code='BEANS-250' AND sold_on=DATE '2026-09-15';
