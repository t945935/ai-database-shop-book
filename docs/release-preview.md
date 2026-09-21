# 伴讀預覽

目前公開取得方式是從本 repo 取得 `companion/` 原始檔並直接執行；下列 ZIP 是作者工作區的驗證產物，尚未作為 GitHub Release asset 發布。

- 預覽包 SHA256：`dcca77dfec0af4e1bf0d3d3b324d6d577e2b2c0af5779636f2514bec7585d395`
- 本機驗證：PostgreSQL 16.15、Python 3.12.3、psycopg 3.2.10、pytest 8.4.2。
- 完整回歸：103 passed；乾淨解壓副本與 final lab 亦 103 passed。
- 目前範圍：商品／SKU、訂單價格快照、採購收貨練習、單 SKU 庫存、付款事件練習、報表、索引、文件版本引用、deterministic 補貨規則、冪等收貨服務、隔離安全／migration／restore 測試、final lab 與模型無關的唯讀 AI 工具。
- 尚未完成：正式多表服務整合、真實金流、pgvector、真實模型、Docker、權限／migration／備份 Release 驗收、真人試讀。

執行入口：

```bash
cd companion
bash bootstrap_pg.sh
bash run.sh
# 完整交付驗收
bash final_lab.sh
```

目前只驗證 WSL2／Ubuntu 24.04 amd64；請使用虛構資料與隔離環境。