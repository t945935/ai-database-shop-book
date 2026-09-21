-- Fictional September report: preserve every SKU, including inactive ones.
CREATE VIEW demo_september_sales AS
SELECT s.code,
       coalesce(sum(d.qty),0) AS units,
       coalesce(sum(d.qty*d.unit_price),0) AS revenue
FROM sku s
LEFT JOIN demo_sale d
  ON d.sku_code=s.code
 AND d.status='shipped'
 AND d.sold_on >= DATE '2026-09-01'
 AND d.sold_on < DATE '2026-10-01'
GROUP BY s.code;
