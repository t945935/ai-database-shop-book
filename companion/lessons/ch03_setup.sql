-- CHAPTER 03 ONLY: fictional sales facts, NOT a production order schema.
CREATE TABLE demo_sale (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku_code text NOT NULL REFERENCES sku(code) ON DELETE RESTRICT,
    sold_on date NOT NULL,
    status text NOT NULL CHECK (status IN ('shipped','cancelled')),
    qty integer NOT NULL CHECK (qty > 0),
    unit_price numeric NOT NULL CHECK (unit_price >= 0 AND unit_price < 10000000000 AND unit_price = round(unit_price,2))
);

CREATE TABLE demo_tag (
    sku_code text NOT NULL REFERENCES sku(code) ON DELETE RESTRICT,
    tag text NOT NULL,
    PRIMARY KEY (sku_code,tag)
);

INSERT INTO demo_sale(sku_code,sold_on,status,qty,unit_price) VALUES
('COFFEE-250','2026-09-01','shipped',2,320),
('COFFEE-250','2026-09-15','shipped',1,300),
('COFFEE-250','2026-09-30','shipped',1,300),
('FILTER-100','2026-09-10','shipped',3,120),
('COFFEE-250','2026-08-31','shipped',1,999),
('COFFEE-250','2026-10-01','shipped',1,999),
('DRIPPER','2026-09-20','cancelled',1,450);

INSERT INTO demo_tag(sku_code,tag) VALUES
('COFFEE-250','咖啡'),('COFFEE-250','推薦'),('FILTER-100','耗材');
