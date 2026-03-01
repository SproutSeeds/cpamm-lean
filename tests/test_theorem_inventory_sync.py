from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT = ROOT / "scripts" / "theorem_inventory.py"
VERIFICATION = ROOT / "VERIFICATION.md"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


class TheoremInventorySyncTests(unittest.TestCase):
    def test_check_current_verification_sync_passes(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                str(SCRIPT),
                "--root",
                str(ROOT),
                "--verification-md",
                str(VERIFICATION),
                "--check-verification",
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("is in sync", result.stdout)

    def test_check_verification_sync_fails_when_section_is_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_verification = Path(tmp_dir) / "VERIFICATION_BAD_SYNC.md"
            text = VERIFICATION.read_text(encoding="utf-8")
            text = text.replace("- `sim_swapXforY`\n", "", 1)
            bad_verification.write_text(text, encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--verification-md",
                    str(bad_verification),
                    "--check-verification",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("out of sync", result.stdout)
            self.assertIn("sim_swapXforY", result.stdout)

    def test_write_verification_repairs_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            working_verification = Path(tmp_dir) / "VERIFICATION_SYNC_WRITE.md"
            text = VERIFICATION.read_text(encoding="utf-8")
            text = text.replace("- `sim_swapXforY`\n", "", 1)
            working_verification.write_text(text, encoding="utf-8")

            write_result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--verification-md",
                    str(working_verification),
                    "--write-verification",
                ]
            )
            self.assertEqual(write_result.returncode, 0, msg=write_result.stdout + write_result.stderr)
            self.assertIn("updated", write_result.stdout)

            check_result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--verification-md",
                    str(working_verification),
                    "--check-verification",
                ]
            )
            self.assertEqual(check_result.returncode, 0, msg=check_result.stdout + check_result.stderr)
            self.assertIn("is in sync", check_result.stdout)

    def test_inventory_out_file_is_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "theorem-inventory.md"
            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--out",
                    str(out_file),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(out_file.exists())
            text = out_file.read_text(encoding="utf-8")
            self.assertIn("# CPAMM Theorem Inventory", text)
            self.assertIn("Total theorems:", text)


if __name__ == "__main__":
    unittest.main()
