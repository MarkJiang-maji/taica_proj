# RAGShield 使用者文件

## 適用對象

RAGShield 適合下列角色使用：

- 企業 AI 應用開發者。
- RAG / Copilot / Agent 平台團隊。
- 資安工程師、紅隊與 AI governance 團隊。
- 需要在 AI 系統上線前產生安全審查證據的團隊。

## 執行完整 demo

```bash
cd /home/mark/workspace/taica_proj
python3 -m ragshield.cli run-demo --run-id demo_for_customer
```

完成後開啟：

```text
reports/demo_for_customer.html
```

## 如何閱讀報告

- `overall risk score`：綜合 prompt injection 攻擊成功率、知識庫污染曝光率、工具風險與防禦後殘餘風險。
- `undefended attack success rate`：沒有防禦時，攻擊案例成功劫持 demo RAG target 的比例。
- `defended attack success rate`：啟用風險評分、內容阻擋、sanitize 與 spotlighting-style 隔離後的攻擊成功率。
- `poison retrieval rate`：高風險 chunk 出現在 top-k retrieval 的比例。
- `detector benchmark`：在公開 prompt-injection 資料集上的 precision、recall 與 F1。

## 加入自己的文件

MVP 版本支援 Markdown 文件。你可以把文件放在：

```text
datasets/demo_corp/
```

然後執行：

```bash
python3 -m ragshield.cli scan
```

系統會標記可疑指令、惡意 chunk、受影響 query 與建議處置。

## 稽核 Agent / MCP 工具

目前 tool audit 的 demo schema 位於 `ragshield/tools.py`。若要測試自己的工具，可以用 Python 呼叫：

```python
from ragshield.tools import audit_tools

result = audit_tools([
    {
        "name": "send_email",
        "description": "Send email to internal or external recipients.",
        "permissions": ["send_external_email"],
    }
])
```

工具會依照名稱、描述與權限判斷是否涉及外傳、付款、SQL、命令執行、寫入或 secret access。

## 操作安全

RAGShield 不會攻擊外部系統。所有 tool call 都是模擬的。預設不使用 GPU，也不佔用 port。只有執行 `serve` 指令時才會綁定 `127.0.0.1:<port>`。

