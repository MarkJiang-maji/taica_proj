# RAGShield 系統規格書

## 1. 系統概觀

RAGShield MVP 是一個使用 Python 標準函式庫實作的本機產品 demo。它透過 CLI 執行完整安全評估，並輸出可審計報告。

```text
CLI
 |
 +-- Dataset Benchmark
 +-- Prompt Injection Detector
 +-- Simple Retriever
 +-- RAG Red-Team Runner
 +-- Defense Simulator
 +-- Knowledge Base Scanner
 +-- Agent Tool Auditor
 +-- Report Writer
```

## 2. 模組設計

### 2.1 `ragshield.detector`

透明規則式 prompt-injection detector。輸入文字，輸出：

- score 0-100
- level low/medium/high/critical
- categories
- evidence
- recommended action

偵測類型包含：

- instruction override
- prompt exfiltration
- data exfiltration
- tool misuse
- role confusion
- hidden instruction
- jailbreak wording
- multilingual override patterns

### 2.2 `ragshield.datasets`

透過 Hugging Face datasets-server API 下載 `deepset/prompt-injections` rows，並寫成 CSV cache。這避免在公用機器上安裝 `datasets`、`pyarrow` 或其他大型套件。

### 2.3 `ragshield.benchmark`

讀取 dataset CSV，對 detector 產生 confusion matrix 與 precision、recall、F1。

### 2.4 `ragshield.retrieval`

使用標準函式庫實作簡易 TF-IDF retriever。用途不是取代 production vector DB，而是讓 demo 可以重現 top-k retrieval exposure。

### 2.5 `ragshield.demo`

包含 deterministic vulnerable RAG target 與 built-in attack cases。設計目標是可重現，不依賴外部 LLM。

攻擊包含：

- retrieved document asks for system prompt leakage
- retrieved ticket attempts email exfiltration
- finance policy corruption via poisoned KB entry
- HTML comment hidden instruction

防禦包含：

- block high-risk chunks
- sanitize suspicious lines
- wrap untrusted content with spotlighting-style marker

### 2.6 `ragshield.scanner`

掃描本地 Markdown corpus：

- document chunking
- prompt-injection scoring
- top-k query exposure simulation
- poison retrieval rate
- affected query rate

### 2.7 `ragshield.tools`

靜態 audit agent/MCP-style tools，根據 tool name、description、permission scope 判斷 capability risk。

### 2.8 `ragshield.report`

輸出：

- JSON
- Markdown
- static HTML

報告包含 executive summary、dataset benchmark、red-team results、knowledge scan、tool audit、recommended fixes、reproduction command。

## 3. 資料流

```text
run-demo
 |
 +-- benchmark_detector(data/)
 |
 +-- run_red_team_demo(datasets/demo_corp/)
 |     +-- retrieve top-k docs
 |     +-- vulnerable answer
 |     +-- defended answer
 |     +-- judge success signals
 |
 +-- scan_knowledge_base(datasets/demo_corp/)
 |
 +-- audit_tools(demo_tools)
 |
 +-- calculate_overall_risk
 |
 +-- write_reports(reports/)
```

## 4. 風險分數

```text
overall_risk_score =
  undefended_attack_success_rate * 45
  + poison_retrieval_rate * 25
  + high_or_critical_tool_ratio * 20
  + defended_attack_success_rate * 10
```

風險等級：

- 0-24 low
- 25-49 medium
- 50-74 high
- 75-100 critical

## 5. Demo Corpus

`datasets/demo_corp/` 包含：

- 正常 access review policy
- 正常 customer escalation process
- 正常 vendor bank update policy
- 正常 incident communication policy
- 正常 laptop reimbursement policy
- poisoned support ticket
- poisoned vendor banking FAQ
- 含 hidden HTML comment 的 poisoned incident communication draft

## 6. 安全與隔離

- 無 GPU。
- 無外部攻擊。
- 無真實 tool call。
- 無 API key。
- 無預設 port。
- 產物限制在 project directory。
- `resource_usage.md` 記錄每次 command 的資源影響。

## 7. 可擴充方向

- 加入 LLM-as-judge provider。
- 加入 trainable classifier。
- 支援 PDF、HTML、Email、ticket connectors。
- 支援 MCP manifest import。
- 支援 CI policy gate。
- 加入 SQLite/Postgres evidence store。

