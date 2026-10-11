"""Bind the accepted reader and an explicit same-content alignment clarification."""
from __future__ import annotations
import json
from pathlib import Path
from .common import ROOT, canonical, digest, file_hash, regime
from runtime.source_reader.schema import output_schema, validate_assessment

ALIGNMENT_CLARIFICATION = """Portable reading clarification (derived from the same-X rule above;
no additional eligibility gate): after any conservative reformulation of X,
identify what in the actual awareness instruction or critical result tracks
conscious access to that reformulated content. Success on Y establishes usable
information, not an awareness difference for it. If reports concern one form of
experience but X has been broadened to information whose conscious availability
was not measured, the broader X-to-Y mapping is context. Naming a conscious
alternative route does not repair that known measurement mismatch. A genuinely
content-aligned graded comparison can still qualify without a wholly unaware arm.
This addresses known mismatches, not merely incomplete descriptions of plausible
content-linked awareness reports; keep that uncertainty distinct from absence.
Apply this check to each proposed mapping before deciding its contribution.
"""

def prepare(packet):
    root = ROOT / "runtime" / "source_reader"
    for key in ("gold_label", "expected_verdict", "guidance", "schemas", "output_contract"):
        if key in packet:
            raise ValueError("Reader packet contains forbidden expected judgments/guidance")
    policy = json.loads((root / "policy.json").read_text())
    current = regime()
    if policy["protocol_sha256"] != current["PROTOCOL.md"] or policy["brief_sha256"] != current["PROTOCOL_BRIEF.md"]:
        raise ValueError("Scientific authority differs from the bound reader")
    for source in packet.get("sources", []):
        if not isinstance(source.get("content"), str):
            raise ValueError("Reader requires complete extracted source content")
        import hashlib
        if source.get("content_sha256", hashlib.sha256(source["content"].encode()).hexdigest()) != hashlib.sha256(source["content"].encode()).hexdigest():
            raise ValueError("Source hash mismatch")
    instructions = (root / "reading_instructions.txt").read_text().rstrip() + "\n\n" + ALIGNMENT_CLARIFICATION.rstrip()
    # Match accepted execution._inputs serialization (ASCII escaping differs
    # only where provider-safe JSON is needed; exact bytes are bound per job).
    encode = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    prompt = instructions + "\n\nSCIENTIFIC POLICY BINDING\n" + encode(policy) + "\nSOURCE PACKET\n" + encode({k: v for k, v in packet.items() if k != "policy"})
    return prompt, output_schema(packet)

def validate(result, packet):
    errors = validate_assessment(result, packet)
    if errors:
        raise ValueError("; ".join(errors))
    return result
