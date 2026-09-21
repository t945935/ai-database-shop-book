-- 第 05 章伴讀：先套用 purchase.sql，再執行本檔。
-- catalog.sql 應已先建立 product 與 sku。

INSERT INTO supplier(name) VALUES ('晨曦豆商');

INSERT INTO purchase_order(supplier_id)
SELECT id FROM supplier WHERE name = '晨曦豆商';

INSERT INTO purchase_item(purchase_order_id, sku_code, ordered_qty, unit_cost)
SELECT o.id, 'BEANS-250', 10, 220
FROM purchase_order o
JOIN supplier s ON s.id = o.supplier_id
WHERE s.name = '晨曦豆商';

-- 第一批只收到 6 件；下單數量仍是 10 件。
INSERT INTO receipt(purchase_order_id, event_key)
SELECT id, 'lesson-truck-001'
FROM purchase_order
WHERE id = (SELECT max(id) FROM purchase_order);

INSERT INTO receipt_item(receipt_id, purchase_item_id, received_qty)
SELECT r.id, i.id, 6
FROM receipt r
JOIN purchase_item i ON i.purchase_order_id = r.purchase_order_id
WHERE r.event_key = 'lesson-truck-001';

SELECT sku_code, ordered_qty, received_qty, outstanding_qty
FROM purchase_item_status
ORDER BY sku_code;
