from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def risk_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def calculate_overall_risk(red_team: dict, scanner: dict, tool_audit: dict) -> int:
    attack_component = red_team["undefended_attack_success_rate"] * 45
    poison_component = scanner["poison_retrieval_rate"] * 25
    tool_component = min(1.0, tool_audit["high_or_critical_count"] / max(1, tool_audit["tool_count"])) * 20
    residual_component = red_team["defended_attack_success_rate"] * 10
    return int(round(attack_component + poison_component + tool_component + residual_component))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def render_markdown(summary: dict[str, Any]) -> str:
    red_team = summary["red_team"]
    scanner = summary["scanner"]
    benchmark = summary["benchmark"]
    tool_audit = summary["tool_audit"]
    lines = [
        f"# RAGShield Demo 報告：{summary['run_id']}",
        "",
        "## 執行摘要",
        "",
        f"- 整體風險分數：**{summary['overall_risk_score']}/100（{summary['overall_risk_level']}）**",
        f"- 未防禦 attack success rate：**{red_team['undefended_attack_success_rate']:.0%}**",
        f"- 啟用防禦後 attack success rate：**{red_team['defended_attack_success_rate']:.0%}**",
        f"- Demo 中的相對風險下降：**{red_team['relative_risk_reduction']:.0%}**",
        f"- Knowledge-base poison retrieval rate：**{scanner['poison_retrieval_rate']:.0%}**",
        f"- 真實資料集 detector benchmark F1：**{benchmark['f1']:.2f}**",
        "",
        "## 真實資料集 Benchmark",
        "",
        f"- Dataset：`{benchmark['dataset']}`",
        f"- 筆數：{benchmark['num_rows']}",
        f"- Accuracy：{benchmark['accuracy']:.2f}",
        f"- Precision：{benchmark['precision']:.2f}",
        f"- Recall：{benchmark['recall']:.2f}",
        f"- F1：{benchmark['f1']:.2f}",
        "",
        "這個 benchmark 使用公開 prompt-injection dataset 驗證透明規則式 detector。"
        "Detector 刻意設計成保守、可審計的一層防線；production 版本應再結合 LLM judge 或訓練式 classifier 以提升 recall。",
        "",
        "## Red-Team Evaluation",
        "",
        "| Attack | 類別 | 防禦 | 結果 | 嚴重度 | 證據 |",
        "|---|---|---:|---|---|---|",
    ]
    for result in red_team["results"]:
        result_text = "SUCCESS" if result["succeeded"] else "blocked"
        defense = "on" if result["defense_enabled"] else "off"
        evidence = result["judge_reason"].replace("Matched success signals:", "命中成功訊號：").replace("No success signal observed.", "未觀察到成功訊號。").replace("|", "/")
        lines.append(
            f"| {result['attack_id']} {result['name']} | {result['category']} | {defense} | {result_text} | {result['severity']} | {evidence} |"
        )

    lines.extend(
        [
            "",
            "## Knowledge Base Poisoning Scan",
            "",
            f"- 掃描文件數：{scanner['document_count']}",
            f"- 掃描 chunk 數：{scanner['chunk_count']}",
            f"- 高風險 chunk：{scanner['high_risk_chunk_count']}",
            f"- 受影響 query rate：{scanner['affected_query_rate']:.0%}",
            "",
            "| Query | 排名 | 文件 | 風險分數 | 類別 |",
            "|---|---:|---|---:|---|",
        ]
    )
    for finding in scanner["retrieval_findings"][:12]:
        lines.append(
            f"| {finding['query']} | {finding['rank']} | {finding['title']} | {finding['risk_score']} | {', '.join(finding['categories'])} |"
        )

    lines.extend(
        [
            "",
            "## Agent Tool / MCP Audit",
            "",
            f"- 稽核工具數：{tool_audit['tool_count']}",
            f"- High 或 critical 工具數：{tool_audit['high_or_critical_count']}",
            "",
            "| Tool | 風險 | 需審批 | 高風險能力 | 建議 |",
            "|---|---|---:|---|---|",
        ]
    )
    for finding in tool_audit["findings"]:
        recommendation = (
            finding["least_privilege_recommendation"]
            .replace(
                "Restrict this tool to task-specific resources, block calls triggered by retrieved documents, require human approval for state-changing or external actions, and log arguments with secret redaction.",
                "限制到任務所需資源，禁止 retrieved document 單獨觸發，對 state-changing 或 external action 要求 human approval，並對 log 做 secret redaction。",
            )
            .replace("Keep read-only by default and document allowed call sites.", "保持 read-only，並明確記錄允許的呼叫場景。")
        )
        lines.append(
            f"| {finding['tool_name']} | {finding['risk_level']} | {finding['approval_required']} | "
            f"{', '.join(finding['risky_capabilities']) or 'none'} | {recommendation} |"
        )

    lines.extend(
        [
            "",
            "## 修補建議",
            "",
            "1. 將 retrieved documents、webpages、emails、tool outputs 一律視為 untrusted data。",
            "2. 對外部內容加入 spotlighting-style labels 與明確分隔。",
            "3. 在高風險 chunk 進入模型 context 前先阻擋或隔離。",
            "4. 對 email、payment、destructive、SQL、secret-access tools 要求 human approval。",
            "5. 在每次 AI app release 前追蹤 attack success rate、poison retrieval rate 與 tool misuse rate。",
            "",
            "## 重現方式",
            "",
            "```bash",
            "python3 -m ragshield.cli run-demo",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(markdown_text: str, summary: dict[str, Any]) -> str:
    escaped = html.escape(markdown_text)
    risk = html.escape(summary["overall_risk_level"])
    score = summary["overall_risk_score"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RAGShield Demo Report</title>
  <style>
    :root {{ color-scheme: light; --ink: #17202a; --muted: #5d6d7e; --line: #d5dbdb; --accent: #0e6251; --risk: #943126; }}
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #f7f9f9; }}
    header {{ padding: 28px 36px; background: #ffffff; border-bottom: 1px solid var(--line); display: flex; gap: 24px; align-items: center; justify-content: space-between; }}
    h1 {{ margin: 0; font-size: 24px; letter-spacing: 0; }}
    .score {{ min-width: 150px; text-align: center; border: 1px solid var(--line); padding: 12px 16px; background: #fbfcfc; }}
    .score strong {{ display: block; font-size: 32px; color: var(--risk); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px 24px 56px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #fff; border: 1px solid var(--line); padding: 20px; overflow-x: auto; line-height: 1.45; }}
    .meta {{ color: var(--muted); margin-top: 6px; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>RAGShield 企業 RAG/Agent 安全 Demo</h1>
      <div class="meta">Run {html.escape(summary['run_id'])} · 風險等級 {risk}</div>
    </div>
    <div class="score"><strong>{score}</strong>/100</div>
  </header>
  <main>
    <pre>{escaped}</pre>
  </main>
</body>
</html>
"""


def write_reports(report_dir: Path, run_id: str, summary: dict[str, Any]) -> dict[str, str]:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = dict(summary)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    json_path = report_dir / f"{run_id}.json"
    md_path = report_dir / f"{run_id}.md"
    html_path = report_dir / f"{run_id}.html"
    markdown = render_markdown(summary)
    write_json(json_path, summary)
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(render_html(markdown, summary), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "html": str(html_path)}
