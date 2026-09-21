-- Filter membership, not joined sales rows: each SKU stays one report row.
SELECT r.code,r.units,r.revenue
FROM demo_september_sales r
WHERE EXISTS (
    SELECT 1 FROM demo_tag t
    WHERE t.sku_code=r.code AND t.tag IN ('咖啡','推薦')
)
ORDER BY r.code;
