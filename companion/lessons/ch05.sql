-- 第 05 章伴讀：先套用 purchase.sql，再執行本檔。
-- catalog.sql 應已先建立 product 與 sku，且使用 COFFEE-250。

INSERT INTO supplier(name) VALUES ('晨曦豆商');

INSERT INTO purchase_order(supplier_id)
SELECT id FROM supplier WHERE name = '晨曦豆商';

INSERT INTO purchase_item(order_id, sku_code, ordered_qty, unit_cost)
SELECT o.id, 'COFFEE-250', 10, 220
FROM purchase_order o
JOIN supplier s ON s.id = o.supplier_id
WHERE s.name = '晨曦豆商';

INSERT INTO receipt(event) VALUES ('lesson-truck-001');
INSERT INTO receipt_item(receipt_event, purchase_item_id, qty)
SELECT 'lesson-truck-001', id, 4
FROM purchase_item
WHERE sku_code = 'COFFEE-250'
ORDER BY id DESC LIMIT 1;

INSERT INTO receipt(event) VALUES ('lesson-truck-002');
INSERT INTO receipt_item(receipt_event, purchase_item_id, qty)
SELECT 'lesson-truck-002', id, 3
FROM purchase_item
WHERE sku_code = 'COFFEE-250'
ORDER BY id DESC LIMIT 1;

SELECT sku_code, ordered_qty, received_qty, remaining_qty
FROM purchase_item_status
WHERE sku_code = 'COFFEE-250'
ORDER BY id DESC LIMIT 1;
