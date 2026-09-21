-- Fictional chapter 02 data. Requires catalog.sql in an empty schema.
WITH p AS (
    INSERT INTO product(name) VALUES ('日常配方豆') RETURNING id
)
INSERT INTO sku(code,product_id,weight_g,price)
SELECT v.code,p.id,v.weight_g,v.price
FROM p CROSS JOIN (VALUES
    ('COFFEE-250',250,320), ('COFFEE-500',500,600)
) AS v(code,weight_g,price);

WITH p AS (
    INSERT INTO product(name) VALUES ('錐形濾紙') RETURNING id
)
INSERT INTO sku(code,product_id,price)
SELECT 'FILTER-100',id,120 FROM p;

WITH p AS (
    INSERT INTO product(name) VALUES ('陶瓷濾杯') RETURNING id
)
INSERT INTO sku(code,product_id,price)
SELECT 'DRIPPER',id,450 FROM p;

UPDATE sku SET price=350 WHERE code='COFFEE-250';
UPDATE sku SET active=false WHERE code='COFFEE-500';

-- An unused draft variant can be deleted; referenced variants cannot.
INSERT INTO sku(code,product_id,price)
SELECT 'DRAFT-ONLY',product_id,0 FROM sku WHERE code='DRIPPER';
DELETE FROM sku WHERE code='DRAFT-ONLY';

SELECT s.code,p.name,s.weight_g,s.price,s.active
FROM sku s JOIN product p ON p.id=s.product_id
ORDER BY s.code;
