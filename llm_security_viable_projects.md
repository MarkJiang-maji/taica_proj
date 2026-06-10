# RAGShield 產品方向決策書

## 最終選題

本專案選擇實作 **RAGShield: Enterprise RAG / Agent Security Evaluation Platform**。

這不是單純的 prompt filter，也不是只把論文 benchmark 重跑一次，而是一個面向企業 AI 應用的安全評測產品雛形。它能掃描 RAG 知識庫、重放 prompt injection 攻擊、比較防禦前後效果、稽核 agent/MCP tool 權限，並產生可交給資安團隊與主管閱讀的報告。

## 為什麼選這個方向

企業正在把 LLM 接到文件庫、客服票、Email、CRM、財務流程與內部工具。這些資料來源原本只是「資料」，但在 RAG/Agent pipeline 裡會被放進模型 context，實際上變成可能影響模型行為的半控制平面。

攻擊者只要能放入一份惡意文件、票單、網頁或 tool output，就可能誘導模型：

- 洩漏 system prompt 或內部指令。
- 外傳敏感資料。
- 產生錯誤或被操控的業務回答。
- 呼叫高風險工具，例如寄信、付款、SQL、刪除或執行命令。

RAGShield 的商業價值來自四個企業會真的在意的問題：

1. 我的 RAG app 會不會被 indirect prompt injection 劫持？
2. 哪些知識庫文件會污染 top-k retrieval？
3. 防禦層上線前後，攻擊成功率下降多少？
4. 哪些 agent tools 需要 least privilege、human approval 或禁止由 retrieved content 觸發？

## 研究依據與產品轉譯

| 研究或資源 | 核心啟發 | RAGShield 的落地方式 |
|---|---|---|
| OWASP Top 10 for LLM Applications 2025 | Prompt injection、sensitive information disclosure、excessive agency 是企業治理議題。 | 報告以資安團隊能理解的風險分類、證據與修補建議呈現。 |
| Formalizing and Benchmarking Prompt Injection Attacks and Defenses | Prompt injection 需要可比較的攻擊、防禦與評測方法。 | 建立 attack success rate、defended ASR 與 judge evidence。 |
| AgentDojo | Agent task、tool 與 attack 必須一起評估，才貼近真實風險。 | Demo 包含 tool-use exfiltration 與 state-changing tool policy。 |
| Spotlighting | 外部內容應明確標記為 untrusted data。 | 實作 spotlighting-style labeling、sanitize 與 block。 |
| PoisonedRAG | 知識庫污染會透過 retrieval 操控 RAG 回答。 | 實作 high-risk chunk scan 與 poison retrieval rate。 |
| InjecAgent / Agent Security Bench / MCP Security Bench | 工具與 MCP 擴大了 LLM 系統的實際破壞面。 | 實作 tool/MCP capability audit 與 approval policy。 |
| deepset/prompt-injections | Detector 需要真實資料集驗證。 | 產生 precision、recall、F1 benchmark。 |

## MVP 成品

本專案已實作：

- `python3 -m ragshield.cli benchmark`
  - 下載並快取公開資料集 `deepset/prompt-injections`
  - 輸出 detector accuracy、precision、recall、F1
- `python3 -m ragshield.cli scan`
  - 掃描 demo enterprise knowledge base
  - 找出 prompt injection / poisoning chunk
  - 計算 poison retrieval rate
- `python3 -m ragshield.cli run-demo`
  - 執行完整 red-team attack suite
  - 比較防禦前後 attack success rate
  - 執行 tool/MCP audit
  - 產生 JSON、Markdown、HTML 報告
- `python3 -m ragshield.cli serve --port 8765`
  - 選配本機靜態報告展示

## 驗證結果

最新 `final_validation` 顯示：

- 真實資料集 benchmark：662 rows，accuracy 0.79，precision 1.00，recall 0.48，F1 0.65。
- RAG red-team demo：未防禦 attack success rate 100%，啟用防禦後 0%。
- Knowledge scan：8 份 demo 文件中找到 3 個高風險 chunk。
- Tool audit：4 個工具中有 3 個被標記為 high risk，需要 approval 或 least privilege redesign。

## 商業包裝

產品可以 pitch 給：

- 雲端資安公司：作為 AI security posture management 模組。
- Enterprise search / RAG 平台：作為文件上架前安全掃描與 red-team gate。
- AI agent 平台：作為 tool permission auditor 與 runtime guard。
- GRC / AI governance 公司：作為可追溯的 AI app risk evidence generator。

一句話：

> RAGShield 協助企業在 AI 助理上線前，證明它是否會被不可信內容劫持。

