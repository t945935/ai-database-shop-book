SELECT sku_code, period_start, gross_profit,
       rank() OVER (
           PARTITION BY period_start
           ORDER BY gross_profit DESC
       ) AS profit_rank
FROM ch10_monthly_operations
WHERE period_start = DATE '2026-09-01'
ORDER BY profit_rank, sku_code;
