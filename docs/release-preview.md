# 伴讀預覽

目前公開的是未正式出版的伴讀 preview，不是完整書稿或 production ERP。

- 預覽包 SHA256：`1040d2d57f5df9eb4db8c1de26f211670a5acbdd0b64b707b3899f47769ebd78`
- 本機驗證：PostgreSQL 16.15、Python 3.12.3、psycopg 3.2.10、pytest 8.4.2。
- 完整回歸：83 passed；乾淨解壓副本亦 83 passed。
- 目前範圍：商品／SKU、訂單價格快照、採購收貨練習、單 SKU 庫存、付款事件練習、報表、索引與模型無關的唯讀 AI 工具。
- 尚未完成：正式多表服務整合、真實金流、pgvector、真實模型、Docker、權限／migration／備份 Release 驗收、真人試讀。

執行入口：

```bash
cd companion
bash bootstrap_pg.sh
bash run.sh
```

目前只驗證 WSL2／Ubuntu 24.04 amd64；請使用虛構資料與隔離環境。