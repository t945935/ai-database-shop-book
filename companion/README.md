# PostgreSQL 進銷存教學原型：第 02–16 章伴讀

這是單店、單倉、TWD、整數件數的**教學驗證**，不是正式 ERP。每次業務操作只處理一個 SKU；沒有 SQLite、假資料庫或假 API。測試會真的建立 PostgreSQL cluster，再以 psycopg 連線執行 SQL。

## 第 02–13 章新增內容

- `catalog.sql`：商品與 SKU，主鍵／外鍵／價格及重量約束。
- `purchase.sql`：供應商、採購單、分批收貨與未收量練習。
- `order.sql`、`payment.sql`：訂單快照、付款事件與履約狀態練習。
- `ai_tools.py`：模型無關的唯讀白名單工具；真實模型未接入。
- `replenishment.py`：模型無關、無副作用的補貨規則；尚未建立採購確認服務。
- `final_lab.sh`：保存完整回歸的 final lab wrapper。
- `lessons/ch14_documents.sql`：文件版本、生效期間與可引用段落練習。
- `tests/test_security_migrations.py`：隔離角色、migration rollback 與 dump restore 驗收。
- `lessons/ch02.sql`：目錄新增、改價、停售及移除未使用草稿。
- `lessons/ch03_setup.sql`：虛構銷售與 SKU 標籤，**不是正式訂單模型**。
- `lessons/ch03_report.sql`：保留零銷售 SKU 的固定九月練習報表。
- `lessons/ch03_tag_filter.sql`：用 EXISTS 篩標籤，避免重複加總。
- `tests/test_printed_sql.py`：第三章正文查詢的字面快照及結果驗證；編輯流程另外核對正文與快照相同。

目錄模型尚未接入 P1 的 `balance.sku`：它目前仍沒有指向 `sku.code` 的外鍵。P1 庫存原型與本次目錄／報表是不同教學階段，不能宣稱收貨已自動驗證目錄。

本章所有 SQL 檔只套用到空的教學 schema；不提供既有資料庫升級或正式資料 migration。每次測試重建環境，不代表 INSERT 腳本可在同一資料庫任意重送。

```bash
bash run.sh tests/test_catalog.py tests/test_lessons.py
bash run.sh tests/test_reports.py tests/test_teaching_regressions.py
bash run.sh tests/test_printed_sql.py
```

仍以 WSL2／Ubuntu 24.04 amd64 已有 Python 與 uv 為前置。下方完整入口適用，沒有新增依賴。

## 已實測環境與重跑

2026-09-21：WSL2 / Ubuntu 24.04 amd64；Python 3.12.3、uv 0.12.13、PostgreSQL 16.15（Ubuntu `16.15-0ubuntu0.24.04.1`）、psycopg 3.2.10、pytest 8.4.2。其他 OS、架構、Python minor version 尚未驗證。

前置：現有 Python 3.12、uv、Ubuntu `apt-get` / `dpkg-deb`、網路、一般使用者帳號。不要以 root 執行。此方案不需要 Docker、sudo 或 PostgreSQL 系統服務。uv 安裝方式不在本原型驗證範圍；本機已提供 `/home/j5/.hermes/bin/uv`。

本機精確入口：

```bash
cd /home/j5/ai-database-shop-book/companion
bash bootstrap_pg.sh
bash run.sh
```

`bootstrap_pg.sh` 用 `apt-get download` 下載固定版本的 server、client、libpq Debian 套件，校驗 `pg-packages.sha256` 後，以 `dpkg-deb -x` 解壓到專案外的 `$HOME/.cache/shop-pg16`。不安裝套件、不更改系統服務。套件版本若已被 Ubuntu repository 下架，會失敗並停止；不可默默升級冒充相同驗證。該目錄須由自己控制，不能用不可信的共享 cache。

`run.sh` 執行 `uv run --frozen python run_tests.py`，使用 `uv.lock` 建立 `.venv`，設定隔離 libpq 搜尋路徑。可從任意工作目錄呼叫：

```bash
bash /home/j5/ai-database-shop-book/companion/run.sh
# 單一測試；仍使用全新 PostgreSQL cluster
bash /home/j5/ai-database-shop-book/companion/run.sh -k parallel_reserve
# 其他機器已有 uv 時明確指定
UV=/absolute/path/to/uv bash run.sh
```

`PG_CACHE=/absolute/cache/path` 可替換快取，bootstrap 與 run 必須使用相同值。若提供自己的 PostgreSQL binaries，可用 `PG_BIN=/absolute/path/to/bin`，但其他版本尚未驗證。

## 隔離、安全與清理

- 每次 runner 建立 `/tmp/shop-p1-*` 私有暫存目錄（0700），新 cluster 與 Unix socket 都放在裡面。
- 固定 socket port 55439 **不是 TCP 監聽埠**：`listen_addresses=''` 完全關閉 TCP，隨機私有 socket 路徑避免碰撞。沒有連到現有使用者資料庫。
- 本機 socket 使用 trust，host authentication 為 reject。這只是同一 OS 使用者可存取的教學 cluster，不是部署安全設定。
- 每個測試使用 UUID schema；測後 drop。runner 在 `finally` 停止 server，正常結束後刪除該次暫存 cluster。測試成功與失敗都會清理。
- 若程序被 SIGKILL／主機斷電，可能留下暫存 cluster；以輸出中的**該次** data 路徑執行 `PG_BIN/pg_ctl -D /tmp/shop-p1-該次/data -m fast -w stop`，確認後只刪該目錄，勿批次刪其他資料。
- `.venv`、Python/pytest cache 可刪後重建。PostgreSQL 套件快取保留，非業務資料；不要打包到讀者產物。

## API 與實際資料表

| 入口 | 意義 |
|---|---|
| `receive(dsn, event, sku, qty, unit_cost)` | 合格收貨；unit_cost 用字串、整數或 Decimal，拒絕 float |
| `reserve(connection, event, sku, qty)` | 保留；呼叫者提供 psycopg connection；交易若已存在則使用 savepoint，外層仍須提交 |
| `ship(dsn, event, reservation_event)` | 全數消耗該次保留，保存出貨成本總額快照 |
| `restock(dsn, event, shipment_event, qty)` | 已驗收可再售退貨，引用原出貨成本；不是退款 |
| `stock(dsn, sku)` | `(實體, 保留, 可售, 成本總額, 平均成本)`；不存在回傳 None |
| `reconcile(dsn)` | 只回傳差異列；空 list 表示無差異 |

實際 schema 以 `schema.sql` 為準：`balance` 是 SKU 餘額，`reservation` 為保留來源與 consumed 狀態，`shipment` 為出貨快照，`returned` 為退貨紀錄，`ledger` 為包含實體／保留／成本增減的流水。這不是全書的完整商品／訂單／採購 schema。

`ledger.event` 為全域冪等鍵，所有事件共用命名空間。相同鍵＋相同業務 payload 不重複生效；不同 payload 拒絕。key advisory transaction lock 可涵蓋同鍵但不同 SKU 的競爭；SKU 列鎖保護可售檢查、餘額與成本；出貨鎖保留來源、退貨鎖原出貨，所有相依更新與流水同一交易提交。採 PostgreSQL 預設 READ COMMITTED。

`reconcile` 每列為 `(sku, 實體餘額減流水, 保留餘額減流水, 成本餘額減流水, 保留餘額減未消耗保留來源)`。一次 SQL 使用一致 statement snapshot，不自動更正差異。

## 成本精度與尾差

- 成本總額／成本異動：`NUMERIC(24,6)`，Python Decimal；收貨單價最多六位小數，非負、finite。
- 平均成本以庫存成本總額除實體數量推導，不保存已捨入單價再反覆相乘。零實體的平均成本為零，SQL CHECK 要求零庫存成本為零。
- 出貨成本 = `目前總成本 × 出貨件數 / 目前實體件數`，以 `ROUND_HALF_UP` 捨入到六位小數。清空庫存時會扣完成本總額；分次出貨由最後出貨吸收剩餘成本。
- 原出貨快照為 qty 與成本總額。部分退貨用 `round(原出貨總成本 × 累計退回量 / 原出貨量, 6) - 先前已回補成本`；避免每次獨立捨入導致全退仍有尾差。微小成本下某次退貨的分攤可能為零。全退總額必等於原出貨總額。
- 退貨後以新的成本總額／數量重算平均成本，可能不同於當前平均或原平均。
- 精度是庫存成本教學口徑，不代表付款／發票精度。極端數值、Decimal context 邊界與大型壓力測試尚未驗證；超出 NUMERIC 範圍會由資料庫拒絕。

## 已驗證項目

目前完整套件 **99 passed**；P1 初始紀錄為 32 passed。含 10 輪「兩個已存在的獨立 backend connection 同搶最後一件」，輸出 backend PID，僅一個保留成功；另有並行重送收貨與並行超退測試。

其他測試包含移動加權平均 130、原成本 130 退貨（新進價已變仍沿用原快照）、同鍵 payload 衝突、重複出貨、零庫存尾差、分次全退尾差、DB constraint 故障注入後整個出貨回滾、對帳正常與人為差異、保留來源差異、負庫存和孤兒資料拒絕、非法數量／成本拒絕。

內部證據在上層 `evidence/p1/`，不屬於公開讀者包：`01`–`08` 保存逐步 RED／GREEN，`09-regressions-green.log` 是補充回歸（不是事後偽稱 RED）；`final-green.log` 是正式入口重跑；`clean-copy-green.log` 是無 `.venv` 的新目錄重建並通過，沿用已驗證 PG／uv cache，並非全新 OS 的測試。

第 02–03 章補充證據位於內部 `evidence/p2/`：逐項 RED/GREEN、11 項目錄教學測試、12 項報表及回歸、8 段正文 SQL 查詢，以及完整 63 項回歸。加入約束後的資料庫原生行為及錯誤查詢示範標為補充回歸，不偽稱每一項都曾先 RED。

## 明確未完成

多明細訂單、商品/SKU 與庫存的正式服務整合、採購審批與超收核准、真實付款／退款、退貨驗收 UI、報廢、盤點修復、登入/API/UI、正式權限角色、migration runner、備份還原、pgvector、Docker Compose、AI 供應商、production deployment 均不在本次原型。資料庫所有者仍可直接改寫流水；尚無 append-only 權限保護。不處理死鎖／連線失敗的自動重試、跨 SKU 鎖排序或外部事件佇列。不要把這個入口直接連到正式資料庫。
