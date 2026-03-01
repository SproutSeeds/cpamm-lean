from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT = ROOT / "scripts" / "validate_theorem_inventory.py"
VERIFICATION = ROOT / "VERIFICATION.md"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


class TheoremInventoryValidationTests(unittest.TestCase):
    def test_current_inventory_passes(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                str(SCRIPT),
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("theorem inventory validation passed", result.stdout)
        self.assertIn("(complete mode)", result.stdout)

    def test_missing_theorem_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_verification = Path(tmp_dir) / "VERIFICATION_BAD.md"
            text = VERIFICATION.read_text(encoding="utf-8")
            text = text.replace("- `product_pos`", "- `product_pos_typo`", 1)
            bad_verification.write_text(text, encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--verification-md",
                    str(bad_verification),
                    "--root",
                    str(ROOT),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("theorem inventory validation failed", result.stdout)
            self.assertIn("product_pos_typo", result.stdout)

    def test_missing_section_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_verification = Path(tmp_dir) / "VERIFICATION_MISSING_FILE.md"
            text = VERIFICATION.read_text(encoding="utf-8")
            text = text.replace("### `CPAMM/State.lean`", "### `CPAMM/NotAFile.lean`", 1)
            bad_verification.write_text(text, encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--verification-md",
                    str(bad_verification),
                    "--root",
                    str(ROOT),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("section file not found", result.stdout)

    def test_incomplete_section_fails_in_complete_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_verification = Path(tmp_dir) / "VERIFICATION_INCOMPLETE.md"
            text = VERIFICATION.read_text(encoding="utf-8")
            text = text.replace("- `sim_swapXforY`\n", "", 1)
            bad_verification.write_text(text, encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--verification-md",
                    str(bad_verification),
                    "--root",
                    str(ROOT),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing from VERIFICATION.md inventory", result.stdout)
            self.assertIn("sim_swapXforY", result.stdout)

    def test_allow_incomplete_mode_skips_completeness_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            incomplete_verification = Path(tmp_dir) / "VERIFICATION_INCOMPLETE_ALLOWED.md"
            text = VERIFICATION.read_text(encoding="utf-8")
            text = text.replace("- `sim_swapXforY`\n", "", 1)
            incomplete_verification.write_text(text, encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--verification-md",
                    str(incomplete_verification),
                    "--root",
                    str(ROOT),
                    "--allow-incomplete",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("(listed-only mode)", result.stdout)


if __name__ == "__main__":
    unittest.main()
