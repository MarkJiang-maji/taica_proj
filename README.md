# RAGShield

RAGShield 是一個針對企業 RAG、LLM Agent 與 MCP-style 工具流程的本機安全評測原型。它把近年 prompt injection、RAG poisoning、Agent tool hijacking 的研究轉成可執行 demo，並輸出可驗證的 JSON、Markdown、HTML 報告。

## 這個專案證明什麼

- 企業 RAG 助理可能被知識庫、客服票單、文件或網頁中的惡意指令劫持。
- 高風險 retrieved content 需要被視為不可信資料，而不是模型應該服從的指令。
- 透過風險評分、內容隔離、spotlighting-style 標記與 tool approval policy，可以明顯降低 demo 攻擊成功率。
- 不只用自編樣本，也使用真實公開資料集 `deepset/prompt-injections` 驗證 detector 的 precision、recall 與 F1。
- Agent/MCP 工具需要檢查是否具備外傳資料、付款、SQL、執行命令、刪除或讀取 secret 等高風險能力。

## 快速開始

```bash
cd /home/mark/workspace/taica_proj
python3 -m unittest discover -s tests
python3 -m ragshield.cli run-demo
```

執行後會在 `reports/` 產生報告。HTML 報告可以直接用瀏覽器開啟，不需要啟動伺服器。

如果需要用本機 HTTP 方式展示報告，可以執行：

```bash
python3 -m ragshield.cli serve --port 8765
```

這個指令只會綁定 `127.0.0.1`，資源使用會記錄在 `resource_usage.md`。

如果需要互動式 demo dashboard，可以執行：

```bash
python3 -m ragshield.cli web-demo --port 8787
```

然後開啟：

```text
http://127.0.0.1:8787/
```

## 常用指令

```bash
python3 -m ragshield.cli benchmark
python3 -m ragshield.cli scan
python3 -m ragshield.cli run-demo --run-id customer_pitch
python3 -m ragshield.cli web-demo --port 8787
python3 -m ragshield.cli serve --port 8765
```

可選本機 LLM judge：

```bash
ollama pull qwen3:4b
python3 -m ragshield.cli llm-validate --model qwen3:4b
```

## Demo 輸出

- `reports/<run_id>.json`：給機器讀取的完整 evidence 與 metrics。
- `reports/<run_id>.md`：給工程與資安團隊審查的 Markdown 報告。
- `reports/<run_id>.html`：給簡報或客戶展示使用的靜態報告。
- `resource_usage.md`：記錄公用機器上的網路、port、GPU、檔案寫入狀態。

## 真實資料集

Detector benchmark 使用公開 Hugging Face 資料集 `deepset/prompt-injections`。資料集共有 662 筆，欄位包含 `text` 與 `label`。下載器透過 Hugging Face datasets-server API 取得資料，並快取到：

```text
data/deepset_prompt_injections.csv
```

## 目前驗證結果

最新 `final_validation` 結果：

- Detector benchmark：accuracy 0.79、precision 1.00、recall 0.48、F1 0.65。
- RAG red-team：未防禦 attack success rate 100%，啟用防禦後 0%。
- Knowledge-base scan：demo corpus 中找到 3 個高風險 chunk。
- Tool audit：4 個工具中有 3 個需要 human approval 或 least-privilege redesign。

## 專案結構

```text
ragshield/                 Python package
datasets/demo_corp/        企業情境 demo 知識庫
data/                      公開資料集 CSV 快取
reports/                   產生的報告
reports/screenshots/       final_project.md 引用的網站截圖
web/                       互動式 demo dashboard
docs/                      使用者文件、pitch、架構文件
tests/                     標準函式庫 unittest 測試
final_project.md           完整期末專案論文式說明
```
