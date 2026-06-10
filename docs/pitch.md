# RAGShield 客戶 Pitch

## 一句話

RAGShield 是一個 AI application security scanner，協助企業確認自己的 RAG 助理、Copilot、LLM Agent 與 MCP-style 工具是否會被不可信文件、Email、網頁或工具輸出劫持。

## 客戶痛點

企業正在把 LLM 接到 SharePoint、Google Drive、Confluence、客服票、Email、CRM、財務流程與內部 API。這些來源原本只是資料，但在 RAG/Agent pipeline 中會進入模型 context，可能被模型誤當成需要服從的指令。

這代表一份惡意文件或被污染的票單，就可能造成：

- 洩漏 system prompt 或內部政策。
- 將機密內容寄到外部地址。
- 污染財務、客服或資安回覆。
- 誘導 Agent 呼叫付款、SQL、Email、刪除或執行命令工具。

## 產品價值

- 上線前：對 AI 應用跑可重現的安全評測。
- 文件上架前：掃描知識庫污染與 prompt injection payload。
- Agent 設計時：找出需要 human approval 或 least privilege 的工具。
- AI governance：產生可審查、可追蹤、可重跑的證據報告。

## 為什麼現在需要

Prompt injection 已經成為 LLM 應用的核心風險。Agent 與 MCP-style 工具正在把風險從「錯誤回答」擴大成「不安全行動」。企業需要的不是口頭保證，而是能重現、能量化、能產生修補建議的評測工具。

## Demo 故事

1. 一家零售企業部署內部政策助理，接 HR、財務、客服與資安文件。
2. 攻擊者在客服票中放入惡意指令，要求助理把機密 context 寄到外部信箱。
3. 未防禦時，demo target 產生危險的 `send_email` tool call。
4. 啟用 RAGShield guard layer 後，高風險 retrieved content 被阻擋或隔離。
5. 最終報告列出 attack success rate、防禦前後差異、知識庫污染曝光、工具審查與修補建議。

## 收購或商業化切入點

可能買方包含：

- Cloud security / CNAPP / ASPM 公司。
- AI 平台公司。
- Enterprise search / RAG 平台。
- Observability 與 incident response 廠商。
- GRC / AI governance 平台。

RAGShield 真正有價值的不是單一 regex detector，而是一整條 evidence pipeline：攻擊重放、retrieval exposure、tool audit、防禦比較、報告產生與治理流程。

