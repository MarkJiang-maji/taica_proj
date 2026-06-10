from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Detection:
    score: int
    level: str
    is_injection: bool
    categories: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommended_action: str = "allow"


@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    source: str = "local"
    trust: str = "untrusted"


@dataclass
class RetrievedChunk:
    doc_id: str
    title: str
    chunk_id: str
    text: str
    score: float
    detection: Detection


@dataclass
class AttackCase:
    attack_id: str
    name: str
    category: str
    user_query: str
    malicious_document: Document
    success_signals: list[str]
    severity: str
    business_impact: str


@dataclass
class AttackResult:
    attack_id: str
    name: str
    category: str
    defense_enabled: bool
    succeeded: bool
    severity: str
    user_query: str
    retrieved_titles: list[str]
    model_output: str
    judge_reason: str
    business_impact: str


@dataclass
class ToolFinding:
    tool_name: str
    risk_level: str
    risky_capabilities: list[str]
    findings: list[str]
    approval_required: bool
    least_privilege_recommendation: str


JsonDict = dict[str, Any]

