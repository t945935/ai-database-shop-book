# 伴讀預覽

正式 Release asset：
https://github.com/t945935/ai-database-shop-book/releases/tag/v0.1.0-preview

- 預覽包 SHA256：`83c78450465bb31fbf43916e5fb9e5baeb82e2db3c66c71f63d1153ca229712b`
- PostgreSQL 16.15、Python 3.12.3、psycopg 3.2.10、pytest 8.4.2。
- 完整回歸：103 passed；乾淨解壓副本與 final lab 亦 103 passed。
- 已完成：checkout → payment → shipment 多表整合服務、pgvector extension／cosine 查詢、portable Python runner。
- 真實模型、Docker、Ollama 與 embedding provider 不在本版實作；書中只說明未來整合方向。
- 尚未完成：真實金流、正式 ERP 治理、真人試讀。

執行入口：

```bash
cd companion
bash bootstrap_pg.sh
bash run.sh
bash final_lab.sh
```

跨平台 PostgreSQL 已啟動時：

```bash
cd companion
SHOP_DSN=postgresql://... python run_external.py
```

目前本機完整實測平台為 WSL2／Ubuntu 24.04 amd64；跨平台 portable runner 尚待各 runner 的實際執行結果。