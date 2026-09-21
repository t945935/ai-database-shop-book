CREATE INDEX demo_sale_sku_date_idx ON demo_sale(sku_code,sold_on);
ANALYZE demo_sale;
