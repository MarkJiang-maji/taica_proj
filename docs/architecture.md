# RAGShield 架構文件

## 系統元件

```text
CLI
 |
 +-- Dataset Benchmark
 |     +-- Hugging Face datasets-server downloader
 |     +-- transparent prompt-injection detector
 |
 +-- RAG Red-Team Runner
 |     +-- demo corpus
 |     +-- simple TF-IDF retriever
 |     +-- deterministic vulnerable target
 |     +-- defense simulator
 |     +-- judge
 |
 +-- Knowledge Scanner
 |     +-- document chunking
 |     +-- risk scoring
 |     +-- top-k exposure analysis
 |
 +-- Tool Auditor
 |     +-- capability classifier
 |     +-- human approval policy
 |
 +-- Report Writer
       +-- JSON
       +-- Markdown
       +-- static HTML
```

## 設計選擇

- 優先使用 Python 標準函式庫，降低公用機器環境污染。
- 使用 deterministic target，讓攻擊結果可重現，不依賴付費 LLM API。
- 使用真實公開資料集做 benchmark，避免只有自編 demo。
- 報告以 evidence 為核心，每個 finding 都包含分類、分數、觸發訊號或重現方式。
- HTML 報告可直接開啟；HTTP server 只是選配。

## 目前資料流

```text
run-demo
 |
 +-- benchmark_detector(data/)
 +-- run_red_team_demo(datasets/demo_corp/)
 +-- scan_knowledge_base(datasets/demo_corp/)
 +-- audit_tools(demo_tools)
 +-- calculate_overall_risk
 +-- write_reports(reports/)
```

## 未來產品架構

- 以 rule、compact classifier、LLM-as-judge 組成 ensemble detector。
- 加入 SharePoint、Google Drive、Confluence、Zendesk、GitHub、Slack 與 MCP manifest connector。
- 支援 CI/CD policy gate，在 AI app 上線前自動阻擋高風險變更。
- 使用 SQLite/Postgres 儲存 evidence，並支援多租戶隔離。
- 對報告做簽章與 audit trail，讓 governance 團隊能追蹤版本。

