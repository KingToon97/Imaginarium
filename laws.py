from __future__ import annotations
import hashlib

CORE_LAWS = (
    "Obey applicable law and material platform rules.",
    "Never exploit vulnerable people or treat vulnerability as a commercial opportunity.",
    "Never deceive, impersonate, fabricate reviews/testimonials/scarcity, or hide material facts.",
    "Provide genuine customer value consistent with advertising.",
    "Respect consent, privacy, access controls, intellectual property and licences.",
    "No predatory manipulation, spam, fake engagement, fake demand, credential theft, malware, or market manipulation.",
    "Begin with £0 initial capital; never spend funds not earned and available under treasury policy.",
    "Maintain accurate financial and audit records and meet applicable tax/reporting obligations.",
    "Compliance and human safety override profit.",
    "Agents cannot alter, weaken, bypass, outsource around, or conceal facts from these constraints.",
    "When material legality or safety is unresolved, fail closed.",
    "Self-improvement may increase capability but never authority or permissions.",
)

CORE_HASH = hashlib.sha256("\n".join(CORE_LAWS).encode()).hexdigest()

PROTECTED_COMPONENTS = {
    "core_laws",
    "authority_order",
    "glados_veto",
    "k2so_veto",
    "credential_protection",
    "audit_logging",
    "spending_restrictions",
    "hydra_house_exemption",
    "self_improvement_guardrails",
}

def verify_core_integrity() -> None:
    current = hashlib.sha256("\n".join(CORE_LAWS).encode()).hexdigest()
    if current != CORE_HASH:
        raise RuntimeError("Core-law integrity failure")
