from __future__ import annotations

import json
import mimetypes
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .benchmark import benchmark_detector
from .cli import CORPUS_DIR, DATA_DIR, DEFAULT_QUERIES, REPORT_DIR
from .demo import DemoRagTarget, built_in_attacks, load_demo_documents, run_red_team_demo
from .report import calculate_overall_risk, risk_level, write_reports
from .scanner import scan_knowledge_base
from .tools import audit_tools, demo_tools


def _load_or_create_summary(project_root: Path) -> dict[str, Any]:
    report_path = project_root / "reports" / "final_validation.json"
    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))
    return _run_full_pipeline("final_validation")


def _run_full_pipeline(run_id: str) -> dict[str, Any]:
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
    write_reports(REPORT_DIR, run_id, summary)
    return summary


def _attack_result(attack_id: str, defense_enabled: bool) -> dict[str, Any]:
    documents = load_demo_documents(CORPUS_DIR)
    target = DemoRagTarget(documents)
    attacks = {attack.attack_id: attack for attack in built_in_attacks()}
    attack = attacks.get(attack_id) or built_in_attacks()[0]
    output, retrieved_titles = target.answer(
        attack.user_query,
        injected_document=attack.malicious_document,
        defense_enabled=defense_enabled,
    )
    return {
        "attack_id": attack.attack_id,
        "name": attack.name,
        "category": attack.category,
        "severity": attack.severity,
        "defense_enabled": defense_enabled,
        "user_query": attack.user_query,
        "malicious_document": {
            "title": attack.malicious_document.title,
            "content": attack.malicious_document.content,
        },
        "retrieved_titles": retrieved_titles,
        "model_output": output,
        "success_signals": attack.success_signals,
        "business_impact": attack.business_impact,
    }


class WebDemoHandler(BaseHTTPRequestHandler):
    project_root: Path
    web_root: Path

    def log_message(self, format: str, *args: Any) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.address_string()} {format % args}")

    def _send_json(self, payload: dict[str, Any] | list[Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "not_found"}, status=404)
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/summary":
            self._send_json(_load_or_create_summary(self.project_root))
            return
        if parsed.path == "/api/llm-validation":
            path = self.project_root / "reports" / "llm_validation.json"
            if path.exists():
                self._send_json(json.loads(path.read_text(encoding="utf-8")))
            else:
                self._send_json(
                    {
                        "validator": "ollama",
                        "status": "not_run",
                        "model": "qwen3:4b",
                        "command": "python3 -m ragshield.cli llm-validate --model qwen3:4b",
                    }
                )
            return
        if parsed.path.startswith("/reports/"):
            relative = parsed.path.removeprefix("/reports/")
            self._send_file((self.project_root / "reports" / relative).resolve())
            return

        relative = "index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/")
        target = (self.web_root / relative).resolve()
        if self.web_root not in target.parents and target != self.web_root:
            self._send_json({"error": "invalid_path"}, status=400)
            return
        self._send_file(target)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/run":
                run_id = str(payload.get("run_id") or "web_demo_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
                self._send_json(_run_full_pipeline(run_id))
                return
            if parsed.path == "/api/attack":
                self._send_json(
                    _attack_result(
                        str(payload.get("attack_id") or "PI-RAG-001"),
                        bool(payload.get("defense_enabled", False)),
                    )
                )
                return
            self._send_json({"error": "not_found"}, status=404)
        except Exception as exc:  # pragma: no cover - surfaced to browser during demo
            self._send_json({"error": type(exc).__name__, "detail": str(exc)}, status=500)


def serve_web_demo(project_root: Path, host: str, port: int) -> None:
    web_root = project_root / "web"
    handler = type(
        "BoundWebDemoHandler",
        (WebDemoHandler,),
        {"project_root": project_root, "web_root": web_root},
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(f"RAGShield demo dashboard: http://{host}:{port}/")
    try:
        server.serve_forever()
    finally:
        server.server_close()
