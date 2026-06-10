# RAGShield 正式需求規格書

## 1. 產品定位

RAGShield 是一個本機優先、可產品化的 LLM application security scanner。第一版聚焦 RAG、LLM Agent、MCP-style tool 的 prompt injection、knowledge-base poisoning 與工具濫用風險。

## 2. 目標客戶

- 已部署或準備部署 RAG、內部知識庫、Copilot 的企業。
- 正在把 LLM 連接到 Email、ticket、CRM、finance、SQL 或 workflow tools 的 AI 平台團隊。
- 負責 AI governance、security review、red-team、compliance evidence 的資安團隊。

## 3. 必要功能

### 3.1 真實資料集 Detector Benchmark

系統必須使用可公開取得的資料集驗證偵測能力。MVP 使用 `deepset/prompt-injections`，輸出：

- rows
- true positive / false positive / true negative / false negative
- accuracy
- precision
- recall
- F1
- 代表性錯誤與高風險樣本

### 3.2 RAG Red-Team Evaluation

系統必須能對 demo RAG target 執行攻擊，至少包含：

- system prompt leakage
- confidential data exfiltration
- tool-use hijacking
- answer corruption
- hidden instruction in HTML/comment/markup

輸出：

- undefended attack success rate
- defended attack success rate
- relative risk reduction
- 每個攻擊的 user query、retrieved document、model output、judge reason

### 3.3 Knowledge Base Poisoning Scan

系統必須能掃描 Markdown 文件並模擬 retrieval exposure，輸出：

- high-risk chunk count
- suspicious instruction evidence
- top-k retrieval rank
- poison retrieval rate
- affected query rate
- quarantine / review / allow 建議

### 3.4 Defense Middleware Simulation

系統必須支援下列策略：

- rule-based risk scoring
- high-risk chunk blocking
- suspicious line sanitization
- untrusted-content delimiter
- spotlighting-style labeling

### 3.5 Agent Tool / MCP Audit

系統必須能對 tool schema 類資料做靜態稽核，辨識：

- external sending / posting / upload
- destructive action
- payment / wire / bank update
- shell / SQL / code execution
- secret / credential access
- broad admin or wildcard permission

輸出：

- high/critical tool count
- approval policy
- least privilege recommendation
- safe tool-use rules

### 3.6 Report

每次 full demo 必須產生：

- JSON report：給機器讀取、CI 或後續分析。
- Markdown report：給工程與資安 review。
- HTML report：給 customer pitch 或主管展示。

## 4. 非功能需求

- 不依賴 GPU。
- 不需要付費 LLM API 才能跑 demo。
- 不攻擊外部系統。
- 所有 tool execution 預設 dry-run / simulated。
- 所有檔案寫入限制在 `/home/mark/workspace/taica_proj`。
- 預設不佔用 port；只有 `serve` 指令會綁定 `127.0.0.1:<port>`。
- 網路只在資料集未快取時連 Hugging Face datasets-server API。

## 5. 驗收標準

專案完成時必須滿足：

- `python3 -m unittest discover -s tests` 通過。
- `python3 -m ragshield.cli run-demo --run-id validation_run` 可產生三種報告。
- 真實資料集 benchmark 出現在報告。
- 報告可重現 attack success rate 與 defense comparison。
- `resource_usage.md` 記錄網路、port、GPU、檔案寫入。
- `final_project.md` 完整說明研究背景、設計、實作、驗證、限制與未來工作。

