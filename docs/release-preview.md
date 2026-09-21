# 伴讀預覽

正式 Release asset：
https://github.com/t945935/ai-database-shop-book/releases/tag/v0.1.0-preview

- 預覽包 SHA256：`dcca77dfec0af4e1bf0d3d3b324d6d577e2b2c0af5779636f2514bec7585d395`
- PostgreSQL 16.15、Python 3.12.3、psycopg 3.2.10、pytest 8.4.2。
- 完整回歸：103 passed；乾淨解壓副本與 final lab 亦 103 passed。
- 已完成：checkout → payment → shipment 多表整合服務、pgvector extension／cosine 查詢、portable Python runner。
- 提供但尚未在本機執行：Docker Compose + Ollama `nomic-embed-text` 真實 embedding smoke test。
- 跨平台 CI workflow 已在作者工作區建立；目前 GitHub OAuth credential 缺少 `workflow` scope，故尚未推送 workflow 檔案。
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

真實 embedding model：

```bash
cd companion
docker compose up -d postgres ollama model-init
SHOP_DSN=postgresql://postgres:shop@127.0.0.1:55432/shop python model_smoke.py
```

目前本機完整實測平台為 WSL2／Ubuntu 24.04 amd64；跨平台 portable runner 與 workflow 尚待各 runner 的實際執行結果。