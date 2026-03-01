from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT = ROOT / "scripts" / "intake_validate.py"
SYSTEM_TEMPLATE = ROOT / "Protocol" / "examples" / "cpamm" / "System.json"
HANDOFF_TEMPLATE = ROOT / "Protocol" / "examples" / "cpamm" / "HANDOFF_READY.json"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


class ProtocolIntakeTests(unittest.TestCase):
    def test_template_payloads_pass_strict_gate(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                str(SCRIPT),
                "--system-json",
                str(SYSTEM_TEMPLATE),
                "--handoff-json",
                str(HANDOFF_TEMPLATE),
                "--strict-gate",
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("protocol intake validation passed", result.stdout)

    def test_strict_gate_fails_when_gate_flag_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            handoff = json.loads(HANDOFF_TEMPLATE.read_text(encoding="utf-8"))
            handoff["gate"]["audit_dedup_clear"] = False
            handoff_path = Path(tmp_dir) / "handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--system-json",
                    str(SYSTEM_TEMPLATE),
                    "--handoff-json",
                    str(handoff_path),
                    "--strict-gate",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("strict gate requires value `true`", result.stdout)

    def test_system_validation_fails_on_unknown_write_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            system = json.loads(SYSTEM_TEMPLATE.read_text(encoding="utf-8"))
            system["transitions"][0]["writes"] = ["x_reserve", "unknown_state_var"]
            system_path = Path(tmp_dir) / "system.json"
            system_path.write_text(json.dumps(system), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    str(SCRIPT),
                    "--system-json",
                    str(system_path),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown state var", result.stdout)


if __name__ == "__main__":
    unittest.main()
