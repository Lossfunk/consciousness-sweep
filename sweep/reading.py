"""Bind the source reader and derived, premise-specific reading clarifications."""
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
An article which only reviews or theorizes about experiments is a discovery
lead, not itself an empirical awareness-use prospect. Keep descriptions of
unavailable original experiments as context and identify the originals needed;
do not promote the secondary article because its narrative suggests a comparison.
An article containing its own relevant experiments is assessed normally.

For a proposed negative or nondifference contribution, distinguish a performed
test from an interpretable negative finding. If the supplied source leaves the
critical contrast estimate, analysis population, or comparison coverage
uninterpretable, preserve that test as unresolved; do not call it supporting
negative evidence merely because physical settings were fixed. When that is
the sole proposed contribution, use unresolved or context rather than prospect.
A different source-grounded informative comparison can still qualify with weak
control or uncertain awareness. This implements the existing statistical rule;
it does not require equivalence, Bayesian evidence, or primary-grade control.

Before choosing or narrowing a claim, integrate decision-relevant supporting
and contrary evidence from all supplied sources. For each awareness regime,
distinguish focal observations, transferred results and author interpretations,
then judge their combined support. A donor need not contain the focal X-to-Y
comparison to inform one premise. Explain which task, timing, sample or
sensitivity differences defeat, weaken or leave that transfer reasonable.
Insufficient alone does not mean unable to contribute; similarity or downstream
effects cannot fill absent awareness evidence. Do not discard premise evidence
because the donor's own main claim is context. Include decisive positive and
negative awareness evidence in the existing awareness_evidence and
decisive_evidence fields, keeping sources distinct. State the joint judgment
and its limitation, rather than separate source summaries.

For every proposed narrower mapping, distinguish positive evidence for its
premises from statements that they might hold. Identify what actually varies
in the awareness comparison: reported access to the same content, or the amount,
correctness or identity of information acquired or reported. A report can
establish conscious access to its stated content without making a knowledge-
coverage or correctness score a graded awareness measure of one fixed X.
Locate the task or result evidence supporting use of this X by Y, rather than
only a correlation between reported experience and overall performance.
Apply these checks anew after changing X, Y, subgroup or outcome. A known
construct mismatch belongs in context, not a prospect with a longer caveat.

Locate signal control at the presentation, generation or acquisition of the
focal X, including when Y uses it later. Identical later probes or outcome
displays do not retroactively match the earlier information. A counterintuitive
result for a different Y does not by itself challenge the simple signal account
for this Y. Preserve a coherent tested functional mapping, but do not borrow
another mapping's diagnostic value to promote a separate stronger-input/larger-
effect result. Such a finding may be useful context for an accepted prospect
without independently earning another prospect claim.

For positive as well as negative findings, distinguish an interpretable
observation from a sentence explaining selection or exclusion. If outcome-based
selection or missing critical reporting prevents interpreting the proposed
relation, retain it as unresolved or context rather than promote it by listing
the caveat or assigning low priority. State what information about awareness
and use survives this audit in contribution_reasoning. Uncertain transfer,
plausible function and unmatched internal evidence may remain: no trialwise
report, independent causation, unique mechanism, minimum sample size or
strongest-route control is required. Qualitative and exploratory evidence is
not automatically excluded; neither caveats nor a request for a new experiment
can supply a missing empirical contribution.
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
