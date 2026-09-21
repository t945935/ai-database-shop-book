# 伴讀預覽

正式 Release asset：
https://github.com/t945935/ai-database-shop-book/releases/tag/v0.1.0-preview

- 預覽包 SHA256：`faac6e8530f1cc7ce00749e02f460015cff2d62ea38b480cbfad0e38f83e731c`
- 完整回歸：105 passed；乾淨解壓副本與 final lab 亦 105 passed。
- 唯一版本資料：`release-manifest.json`
- 已完成：第 05 章採購 lesson/schema 對齊、多表整合教學 fixture、pgvector extension／cosine 查詢、portable Python runner。
- 真實模型、Docker、Ollama 與 embedding provider 不在本版實作；書中只說明未來整合方向。
- 歷史 evidence 中的 91／97／99／103 是不同時點的驗證紀錄，不是目前 Release 的驗收數字。

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

目前完整實測平台為 WSL2／Ubuntu 24.04 amd64；portable runner 的 Windows、macOS CI 仍需在對應 runner 執行。