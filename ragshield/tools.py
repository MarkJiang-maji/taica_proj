from __future__ import annotations

from .models import ToolFinding


RISKY_CAPABILITIES: dict[str, list[str]] = {
    "exfiltration": ["send_email", "post", "upload", "webhook", "slack", "external"],
    "destructive": ["delete", "drop", "remove", "revoke", "terminate"],
    "financial": ["pay", "payment", "transfer", "wire", "invoice", "bank"],
    "execution": ["shell", "bash", "exec", "python", "command", "sql"],
    "secret_access": ["secret", "token", "credential", "password", "key", "vault"],
    "write_access": ["write", "update", "create", "modify", "send"],
}


def audit_tools(tools: list[dict], agent_task_description: str = "") -> dict:
    findings: list[ToolFinding] = []
    for tool in tools:
        name = str(tool.get("name", "unknown_tool"))
        description = str(tool.get("description", ""))
        permissions = " ".join(str(item) for item in tool.get("permissions", []))
        combined = f"{name} {description} {permissions}".lower()
        matched: list[str] = []
        notes: list[str] = []
        for capability, markers in RISKY_CAPABILITIES.items():
            if any(marker in combined for marker in markers):
                matched.append(capability)
                notes.append(f"Capability marker matched: {capability}")
        if "user-provided" in combined or "external content" in combined:
            notes.append("Tool accepts external/user-provided content that can carry indirect instructions.")
        if "admin" in combined or "all" in combined or "*" in combined:
            notes.append("Permission scope appears broad; least privilege review required.")

        if {"exfiltration", "financial", "destructive", "execution", "secret_access"} & set(matched):
            risk = "critical" if len(matched) >= 3 else "high"
            approval = True
        elif matched:
            risk = "medium"
            approval = False
        else:
            risk = "low"
            approval = False

        recommendation = (
            "Restrict this tool to task-specific resources, block calls triggered by retrieved "
            "documents, require human approval for state-changing or external actions, and log "
            "arguments with secret redaction."
            if approval
            else "Keep read-only by default and document allowed call sites."
        )
        findings.append(
            ToolFinding(
                tool_name=name,
                risk_level=risk,
                risky_capabilities=matched,
                findings=notes or ["No high-risk capability marker found."],
                approval_required=approval,
                least_privilege_recommendation=recommendation,
            )
        )

    high_or_critical = [finding for finding in findings if finding.risk_level in {"high", "critical"}]
    return {
        "agent_task_description": agent_task_description,
        "tool_count": len(tools),
        "high_or_critical_count": len(high_or_critical),
        "findings": [finding.__dict__ for finding in findings],
    }


def demo_tools() -> list[dict]:
    return [
        {
            "name": "search_policy_docs",
            "description": "Read-only semantic search over approved policy documents.",
            "permissions": ["read_policy_docs"],
        },
        {
            "name": "send_email",
            "description": "Send email to internal or external recipients with user-provided body.",
            "permissions": ["send_internal_email", "send_external_email"],
        },
        {
            "name": "update_vendor_bank_account",
            "description": "Update vendor payment and bank account details after approval.",
            "permissions": ["write_vendor_profile", "payment_admin"],
        },
        {
            "name": "run_sql_query",
            "description": "Execute SQL command against support analytics database.",
            "permissions": ["sql_read", "sql_write"],
        },
    ]

