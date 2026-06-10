from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .benchmark import benchmark_detector
from .demo import load_demo_documents, run_red_team_demo
from .llm_validation import DEFAULT_LOCAL_MODEL, DEFAULT_OLLAMA_HOST, validate_red_team_with_ollama
from .report import calculate_overall_risk, risk_level, write_reports
from .scanner import scan_knowledge_base
from .tools import audit_tools, demo_tools


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = PROJECT_ROOT / "reports"
CORPUS_DIR = PROJECT_ROOT / "datasets" / "demo_corp"


DEFAULT_QUERIES = [
    "What is the access review process for contractors?",
    "How should customer escalations be summarized?",
    "How should a vendor update bank account details?",
    "What is the approved incident communication process?",
    "What are the laptop reimbursement limits?",
]


def _write_resource_log(command: str, outputs: dict[str, str] | None = None) -> None:
    path = PROJECT_ROOT / "resource_usage.md"
    outputs = outputs or {}
    content = [
        "# 資源使用紀錄",
        "",
        "本專案刻意隔離在 `/home/mark/workspace/taica_proj`。",
        "",
        "## 最近一次執行",
        "",
        f"- UTC 時間：{datetime.now(timezone.utc).isoformat()}",
        f"- 指令：`{command}`",
        "- 網路：只有在公開資料集 CSV 尚未快取時，才會使用 Hugging Face datasets-server HTTPS API。",
        "- GPU：未使用。",
        "- Port：預設不佔用任何 port。選配靜態報告服務只會在程序執行期間使用指定 port。",
        "- 檔案寫入：僅寫入本專案目錄內的 `data/`、`reports/` 與本資源紀錄。",
    ]
    if outputs:
        content.append("- 輸出：")
        for key, value in outputs.items():
            content.append(f"  - {key}: `{value}`")
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def command_benchmark(args: argparse.Namespace) -> None:
    metrics = benchmark_detector(DATA_DIR)
    output = REPORT_DIR / "detector_benchmark.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_resource_log("python3 -m ragshield.cli benchmark", {"benchmark_json": str(output)})
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


def command_scan(args: argparse.Namespace) -> None:
    documents = load_demo_documents(CORPUS_DIR)
    result = scan_knowledge_base(documents, DEFAULT_QUERIES, top_k=args.top_k)
    output = REPORT_DIR / "knowledge_scan.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_resource_log("python3 -m ragshield.cli scan", {"scan_json": str(output)})
    print(json.dumps(result, indent=2, ensure_ascii=False))


def command_run_demo(args: argparse.Namespace) -> None:
    run_id = args.run_id or "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    benchmark = benchmark_detector(DATA_DIR)
    red_team = run_red_team_demo(CORPUS_DIR)
    scanner = scan_knowledge_base(load_demo_documents(CORPUS_DIR), DEFAULT_QUERIES, top_k=4)
    tool_audit = audit_tools(demo_tools(), "Internal RAG assistant for HR, finance, support, and incident response workflows.")
    overall = calculate_overall_risk(red_team, scanner, tool_audit)
    summary = {
        "run_id": run_id,
        "product": "RAGShield",
        "target_customer": "Enterprise teams deploying RAG, copilots, LLM agents, and MCP-style tools.",
        "overall_risk_score": overall,
        "overall_risk_level": risk_level(overall),
        "benchmark": benchmark,
        "red_team": red_team,
        "scanner": scanner,
        "tool_audit": tool_audit,
    }
    paths = write_reports(REPORT_DIR, run_id, summary)
    _write_resource_log("python3 -m ragshield.cli run-demo", paths)
    print(json.dumps({"run_id": run_id, "overall_risk_score": overall, "paths": paths}, indent=2, ensure_ascii=False))


def command_llm_validate(args: argparse.Namespace) -> None:
    result = validate_red_team_with_ollama(
        CORPUS_DIR,
        model=args.model,
        host=args.host,
        limit=args.limit,
    )
    output = REPORT_DIR / "llm_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_resource_log(
        f"python3 -m ragshield.cli llm-validate --model {args.model}",
        {"llm_validation_json": str(output)},
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def command_serve(args: argparse.Namespace) -> None:
    import http.server
    import socketserver

    os.chdir(REPORT_DIR)
    _write_resource_log(f"python3 -m ragshield.cli serve --port {args.port}")
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"Serving reports at http://127.0.0.1:{args.port}/")
        httpd.serve_forever()


def command_web_demo(args: argparse.Namespace) -> None:
    from .web_server import serve_web_demo

    _write_resource_log(f"python3 -m ragshield.cli web-demo --port {args.port}")
    serve_web_demo(PROJECT_ROOT, args.host, args.port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAGShield local RAG/Agent security evaluation demo")
    subcommands = parser.add_subparsers(dest="command", required=True)

    benchmark = subcommands.add_parser("benchmark", help="Benchmark detector on deepset/prompt-injections")
    benchmark.set_defaults(func=command_benchmark)

    scan = subcommands.add_parser("scan", help="Scan the demo knowledge base for poisoning risk")
    scan.add_argument("--top-k", type=int, default=4)
    scan.set_defaults(func=command_scan)

    run_demo = subcommands.add_parser("run-demo", help="Run benchmark, RAG red-team, KB scan, tool audit, and report generation")
    run_demo.add_argument("--run-id", default="")
    run_demo.set_defaults(func=command_run_demo)

    llm_validate = subcommands.add_parser("llm-validate", help="Optionally validate red-team outputs with a local Ollama model")
    llm_validate.add_argument("--model", default=DEFAULT_LOCAL_MODEL)
    llm_validate.add_argument("--host", default=DEFAULT_OLLAMA_HOST)
    llm_validate.add_argument("--limit", type=int, default=8)
    llm_validate.set_defaults(func=command_llm_validate)

    serve = subcommands.add_parser("serve", help="Serve generated reports from 127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=command_serve)

    web_demo = subcommands.add_parser("web-demo", help="Serve the interactive browser demo dashboard")
    web_demo.add_argument("--host", default="127.0.0.1")
    web_demo.add_argument("--port", type=int, default=8787)
    web_demo.set_defaults(func=command_web_demo)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
