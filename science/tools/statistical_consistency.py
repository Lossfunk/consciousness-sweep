#!/usr/bin/env python3
"""Reference probabilities from explicit inputs, never scientific classification.

Uses the regularized incomplete beta continued fraction (NIST DLMF 8.17) for
ordinary Student-t and F distributions, and erfc for normal-z. It does not
infer df from N, select a tail, interpret a reported p, or apply an alpha gate.
Bootstrap/permutation/model/cluster conventions are not replaced by these
ordinary distributions. Inputs and source-vs-assumption provenance belong in
the existing source-reading/statistics review receipt.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be an explicit finite number")
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{label} must be finite" + (" and positive" if positive else ""))
    return value


def _beta_fraction(a: float, b: float, x: float) -> float:
    # Modified Lentz evaluation; symmetry in _beta_ratio chooses the stable
    # branch. A failed convergence raises rather than fabricating a probability.
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    result = d
    for m in range(1, 1001):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        c = 1 + aa / c
        if abs(d) < tiny:
            d = tiny
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        result *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        c = 1 + aa / c
        if abs(d) < tiny:
            d = tiny
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        result *= delta
        if abs(delta - 1) < 3e-14:
            return result
    raise ValueError("incomplete beta did not converge within the supported domain")


def _beta_ratio(x: float, a: float, b: float) -> float:
    if x == 0 or x == 1:
        return x
    prefactor = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                         + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1) / (a + b + 2):
        value = prefactor * _beta_fraction(a, b, x) / a
    else:
        value = 1 - prefactor * _beta_fraction(b, a, 1 - x) / b
    if not math.isfinite(value) or not -1e-12 <= value <= 1 + 1e-12:
        raise ValueError("incomplete beta produced an invalid probability")
    return min(1.0, max(0.0, value))


def reference_probability(inputs: dict[str, Any]) -> float:
    """Return the requested signed tail under an explicitly chosen distribution.

    Supported numeric domain: |t/z| <= 1e6, 0 <= F <= 1e12 and
    0 < df <= 1e6. Outside this domain use an appropriate external method and
    document it; this helper's limitation is not an exclusion of a study.
    """
    if not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    distribution = inputs.get("distribution")
    expected = {
        "student-t": {"distribution", "statistic", "df", "tail"},
        "normal-z": {"distribution", "statistic", "tail"},
        "F": {"distribution", "statistic", "df_numerator", "df_denominator", "tail"},
    }
    if not isinstance(distribution, str) or distribution not in expected or set(inputs) != expected[distribution]:
        raise ValueError("distribution and its explicit parameter keys must match the supported format")
    statistic = _number(inputs["statistic"], "statistic")
    tail = inputs["tail"]
    if distribution == "F":
        if tail != "greater" or not 0 <= statistic <= 1e12:
            raise ValueError("F requires the upper tail and 0 <= statistic <= 1e12")
        df1 = _number(inputs["df_numerator"], "df_numerator", positive=True)
        df2 = _number(inputs["df_denominator"], "df_denominator", positive=True)
        if max(df1, df2) > 1e6:
            raise ValueError("df exceeds the helper's supported domain")
        return _beta_ratio(df2 / (df2 + df1 * statistic), df2 / 2, df1 / 2)
    if not isinstance(tail, str) or tail not in {"less", "greater", "two-sided"} or abs(statistic) > 1e6:
        raise ValueError("t/z requires an explicit less/greater/two-sided tail and |statistic| <= 1e6")
    if distribution == "normal-z":
        small_tail = math.erfc(abs(statistic) / math.sqrt(2)) / 2
    else:
        df = _number(inputs["df"], "df", positive=True)
        if df > 1e6:
            raise ValueError("df exceeds the helper's supported domain")
        small_tail = _beta_ratio(df / (df + statistic * statistic), df / 2, .5) / 2
    if tail == "two-sided":
        return 2 * small_tail
    if tail == "greater":
        return small_tail if statistic >= 0 else 1 - small_tail
    return small_tail if statistic <= 0 else 1 - small_tail


def calculation_errors(calculation: Any) -> list[str]:
    """Verify arithmetic/provenance format, not the truth of source attribution."""
    if not isinstance(calculation, dict) or set(calculation) != {"inputs", "basis", "basis_reason", "computed_p"}:
        return ["calculation requires inputs, basis, basis_reason and computed_p"]
    errors = []
    if not isinstance(calculation.get("basis"), str) or calculation.get("basis") not in {"source-reported", "explicit-assumption"}:
        errors.append("calculation must distinguish source-reported parameters from an explicit assumption")
    if not isinstance(calculation.get("basis_reason"), str) or not calculation["basis_reason"].strip():
        errors.append("calculation needs a located parameter basis or named assumption reason")
    try:
        expected = reference_probability(calculation["inputs"])
        actual = _number(calculation["computed_p"], "computed_p")
        if not 0 <= actual <= 1 or not math.isclose(actual, expected, rel_tol=1e-8, abs_tol=0):
            errors.append("computed_p does not match the explicitly supplied reference distribution and tail")
    except (ValueError, OverflowError) as exc:
        errors.append(str(exc))
    return errors


def statistics_observation_errors(value: Any) -> list[str]:
    """Validate factual observations kept inside the existing source receipt."""
    keys = {"measured_outcome", "reported_analysis", "sample_and_unit", "inferential_convention", "numerical_consistency"}
    if not isinstance(value, dict) or set(value) != keys:
        return ["source statistics needs outcome, analysis, sample/unit, convention and numerical consistency"]
    errors = []
    for key in keys - {"numerical_consistency"}:
        if not isinstance(value[key], str) or not value[key].strip():
            errors.append(f"source statistics {key} must be a substantive source observation")
    numerical = value["numerical_consistency"]
    if not isinstance(numerical, dict) or set(numerical) != {"status", "reason", "calculations"}:
        return errors + ["numerical consistency requires status, reason and calculations"]
    if not isinstance(numerical["status"], str) or numerical["status"] not in {"checked", "not-computable", "not-applicable"}:
        errors.append("numerical consistency status is invalid")
    if not isinstance(numerical["reason"], str) or not numerical["reason"].strip():
        errors.append("numerical consistency needs its source-specific interpretation or noncomputation reason")
    calculations = numerical["calculations"]
    if not isinstance(calculations, list):
        return errors + ["calculations must be an array"]
    if numerical["status"] == "checked" and not calculations:
        errors.append("checked numerical consistency requires an explicit calculation")
    if isinstance(numerical["status"], str) and numerical["status"] in {"not-computable", "not-applicable"} and calculations:
        errors.append("a noncomputed observation cannot contain purported completed calculations")
    for calculation in calculations:
        errors.extend(calculation_errors(calculation))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON with explicit distribution parameters")
    args = parser.parse_args()
    try:
        inputs = json.loads(args.input.read_text(encoding="utf-8"))
        result = reference_probability(inputs)
    except (OSError, ValueError, OverflowError) as exc:
        parser.exit(2, f"calculation error: {exc}\n")
    print(json.dumps({"inputs": inputs, "computed_p": result, "scope": "reference probability under explicit inputs; no source, scientific, significance or eligibility inference"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
