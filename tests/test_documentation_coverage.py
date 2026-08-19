from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_documentation", ROOT / "tools" / "validate_documentation.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DocumentationCoverageTests(unittest.TestCase):
    def test_current_documentation_has_complete_structural_coverage(self) -> None:
        errors, stats = MODULE.validate(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(stats["protocol_mapped"], stats["protocol_total"])
        self.assertEqual(stats["agents_mapped"], stats["agents_total"])
        self.assertEqual(stats["unresolved"], 0)

    def test_duplicate_methods_anchor_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "METHODS.md"
            path.write_text(
                '<a id="methods-01"></a>\n## 1. One\n'
                '<a id="methods-01"></a>\n## 2. Two\n',
                encoding="utf-8",
            )
            _sections, errors = MODULE.methods_sections(path)
            self.assertTrue(any("duplicate anchor" in error for error in errors))

    def test_orphan_target_is_detected_by_full_validation(self) -> None:
        crosswalk = ROOT / "docs" / "methods_crosswalk.yaml"
        original = crosswalk.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)
            (scratch / "docs").mkdir()
            for name in ("METHODS.md", "PROTOCOL.md", "AGENTS.md"):
                (scratch / name).write_bytes((ROOT / name).read_bytes())
            (scratch / "docs" / "methods_crosswalk.yaml").write_text(
                original.replace("methods_section: methods-01", "methods_section: methods-stale", 1),
                encoding="utf-8",
            )
            errors, _stats = MODULE.validate(scratch)
            self.assertTrue(any("orphaned METHODS target" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
