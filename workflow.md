# 工作流程紀錄

## 2026-06-10

1. 閱讀原始討論與既有三份規格文件，將方向收斂為企業 RAG / Agent 安全評測平台。
2. 對齊近期研究方向：prompt injection formalization、AgentDojo-style agent evaluation、RAG poisoning、spotlighting-style defense、MCP/tool security。
3. 選擇 `deepset/prompt-injections` 作為公開 benchmark dataset，原因是無需登入、資料量小、適合公用機器快速驗證。
4. 實作 dependency-light Python package：
   - prompt-injection detector
   - Hugging Face dataset downloader
   - detector benchmark
   - simple TF-IDF retriever
   - RAG red-team demo
   - defense simulator
   - knowledge-base scanner
   - tool/MCP auditor
   - JSON / Markdown / HTML report writer
5. 建立企業情境 demo corpus，包含正常政策文件與 poisoned documents。
6. 執行驗證：
   - detector F1：0.65
   - 未防禦 demo ASR：100%
   - 防禦後 demo ASR：0%
   - high-risk chunks：3
   - high/critical tools：3 of 4
7. 補上使用者文件、pitch、架構文件、測試與資源使用紀錄。
8. 將所有 Markdown 文件改寫為中文，保留必要技術名詞、指令與資料集名稱。

