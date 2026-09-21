-- Chapter 10: one row per SKU and reporting period.
-- Revenue, refunds, and cost are aggregated separately before joining.
CREATE VIEW ch10_monthly_operations AS
WITH periods(period_start,period_end) AS (
    VALUES
        (DATE '2026-09-01',DATE '2026-10-01'),
        (DATE '2026-10-01',DATE '2026-11-01')
),
base AS (
    SELECT s.code AS sku_code,p.period_start
    FROM ch10_sku s CROSS JOIN periods p
),
sales AS (
    SELECT s.sku_code,p.period_start,
           sum(s.qty) AS units,
           sum(s.qty*s.unit_price) AS gross_sales
    FROM ch10_sale s
    JOIN periods p ON s.sold_on >= p.period_start AND s.sold_on < p.period_end
    WHERE s.status='shipped'
    GROUP BY s.sku_code,p.period_start
),
refunds AS (
    SELECT s.sku_code,p.period_start,
           sum(r.refund_amount) AS refunds
    FROM ch10_refund r
    JOIN ch10_sale s ON s.id=r.sale_id
    JOIN periods p ON r.refunded_on >= p.period_start AND r.refunded_on < p.period_end
    GROUP BY s.sku_code,p.period_start
),
costs AS (
    SELECT sh.sku_code,p.period_start,
           sum(sh.qty*sh.unit_cost_snapshot) AS cogs
    FROM ch10_shipment sh
    JOIN periods p ON sh.shipped_on >= p.period_start AND sh.shipped_on < p.period_end
    JOIN ch10_sale s ON s.shipment_id=sh.id AND s.status='shipped'
    GROUP BY sh.sku_code,p.period_start
)
SELECT b.sku_code,b.period_start,
       coalesce(sa.units,0) AS units,
       coalesce(sa.gross_sales,0) AS gross_sales,
       coalesce(r.refunds,0) AS refunds,
       coalesce(c.cogs,0) AS cogs,
       coalesce(sa.gross_sales,0)-coalesce(r.refunds,0)-coalesce(c.cogs,0) AS gross_profit
FROM base b
LEFT JOIN sales sa USING (sku_code,period_start)
LEFT JOIN refunds r USING (sku_code,period_start)
LEFT JOIN costs c USING (sku_code,period_start);
