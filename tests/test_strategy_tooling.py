from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


class StrategyToolingTests(unittest.TestCase):
    def test_evidence_portal_generates_files_and_copies_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            portal_out = tmp / "portal"
            commercial_src = tmp / "commercial"
            review_src = tmp / "review"
            commercial_src.mkdir(parents=True, exist_ok=True)
            review_src.mkdir(parents=True, exist_ok=True)

            (commercial_src / "MANIFEST.md").write_text("# Commercial Package\n", encoding="utf-8")
            (commercial_src / "SHA256SUMS").write_text("abc  file.txt\n", encoding="utf-8")
            (commercial_src / "file.txt").write_text("ok\n", encoding="utf-8")
            (review_src / "MANIFEST.md").write_text("# Review Package\n", encoding="utf-8")
            (review_src / "SHA256SUMS").write_text("def  report.log\n", encoding="utf-8")
            (review_src / "report.log").write_text("ok\n", encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/evidence_portal.py",
                    "--input",
                    "strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json",
                    "--portal-dir",
                    str(portal_out),
                    "--commercial-package-dir",
                    str(commercial_src),
                    "--review-package-dir",
                    str(review_src),
                    "--copy-artifacts",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            self.assertTrue((portal_out / "INDEX.md").exists())
            self.assertTrue((portal_out / "STATUS.md").exists())
            self.assertTrue((portal_out / "ARTIFACTS.md").exists())
            self.assertTrue((portal_out / "ASSUMPTIONS_RISKS.md").exists())
            self.assertTrue((portal_out / "FINDINGS.md").exists())
            self.assertTrue((portal_out / "ACCESS.md").exists())
            self.assertTrue((portal_out / "MANIFEST.json").exists())
            self.assertTrue((portal_out / "artifacts/commercial-package/MANIFEST.md").exists())
            self.assertTrue((portal_out / "artifacts/review-package/MANIFEST.md").exists())

            index_text = (portal_out / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("Engagement ID: example-protocol-a-2026q1", index_text)

            artifacts_text = (portal_out / "ARTIFACTS.md").read_text(encoding="utf-8")
            self.assertIn("Commercial Package", artifacts_text)
            self.assertIn("Technical Review Package", artifacts_text)

    def test_evidence_portal_rejects_bad_engagement_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            bad_input = tmp / "bad-input.json"
            payload = json.loads(
                (ROOT / "strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            payload["engagement_id"] = "bad id with spaces"
            bad_input.write_text(json.dumps(payload), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/evidence_portal.py",
                    "--input",
                    str(bad_input),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("engagement_id must be slug-like", result.stdout)

    def test_create_cadence_issue_dry_run_kpi(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/create_cadence_issue.py",
                "--kind",
                "kpi",
                "--reference-date",
                "2026-03-02",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["title"], "[KPI] Weekly Review - 2026-03-02")
        self.assertIn("kpi-review", payload["labels"])
        self.assertEqual(payload["assignees"], [])
        self.assertIn("Week start: 2026-03-02", payload["body"])

    def test_create_cadence_issue_dry_run_risk(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/create_cadence_issue.py",
                "--kind",
                "risk",
                "--reference-date",
                "2026-03-01",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["title"], "[RISK] Register Review - 2026-03-01")
        self.assertIn("risk-review", payload["labels"])
        self.assertIn("Period: 2026-03-01 to 2026-03-31", payload["body"])

    def test_create_cadence_issue_rejects_bad_reference_date(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/create_cadence_issue.py",
                "--kind",
                "kpi",
                "--reference-date",
                "2026-13-99",
                "--dry-run",
            ]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reference date must be YYYY-MM-DD", result.stdout)

    def test_create_cadence_issue_dry_run_with_assignees(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/create_cadence_issue.py",
                "--kind",
                "kpi",
                "--reference-date",
                "2026-03-02",
                "--assignees",
                "alice,bob-1",
                "--notify-webhook-env",
                "CADENCE_NOTIFY_WEBHOOK_URL",
                "--dry-run",
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["assignees"], ["alice", "bob-1"])

    def test_create_cadence_issue_rejects_bad_assignee(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/create_cadence_issue.py",
                "--kind",
                "risk",
                "--assignees",
                "good,bad*name",
                "--dry-run",
            ]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid GitHub assignee login", result.stdout)

    def test_validate_strategy_data_passes_templates(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/validate_strategy_data.py",
                "--pipeline",
                "strategy/assets/crm/PIPELINE_TEMPLATE.csv",
                "--kpi",
                "strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv",
                "--deal-input",
                "strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json",
                "--portal-input",
                "strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json",
            ]
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("strategy data validation passed", result.stdout)

    def test_validate_strategy_data_rejects_bad_pipeline_probability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_pipeline = Path(tmp_dir) / "PIPELINE_BAD.csv"
            text = (
                ROOT / "strategy/assets/crm/PIPELINE_TEMPLATE.csv"
            ).read_text(encoding="utf-8")
            bad_pipeline.write_text(text.replace(",35,", ",135,", 1), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/validate_strategy_data.py",
                    "--pipeline",
                    str(bad_pipeline),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("probability_pct", result.stdout)

    def test_validate_strategy_data_rejects_bad_kpi_percent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_kpi = Path(tmp_dir) / "KPI_BAD.csv"
            text = (
                ROOT / "strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv"
            ).read_text(encoding="utf-8")
            bad_kpi.write_text(text.replace(",97,100,", ",101,100,", 1), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/validate_strategy_data.py",
                    "--kpi",
                    str(bad_kpi),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ci_gate_pass_rate_pct", result.stdout)

    def test_validate_strategy_data_rejects_bad_deal_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_deal = Path(tmp_dir) / "DEAL_BAD.json"
            payload = json.loads(
                (ROOT / "strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            payload["proposal"]["kickoff_date"] = "2026-04-10"
            payload["proposal"]["handoff_date"] = "2026-04-05"
            bad_deal.write_text(json.dumps(payload), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/validate_strategy_data.py",
                    "--deal-input",
                    str(bad_deal),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("kickoff <= midpoint <= handoff", result.stdout)

    def test_validate_strategy_data_rejects_bad_portal_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_portal = Path(tmp_dir) / "PORTAL_BAD.json"
            payload = json.loads(
                (ROOT / "strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            payload["engagement_id"] = "bad id"
            bad_portal.write_text(json.dumps(payload), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/validate_strategy_data.py",
                    "--portal-input",
                    str(bad_portal),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("engagement_id must be slug-like", result.stdout)

    def test_deal_pack_generates_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "deal-pack"
            input_json = ROOT / "strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/deal_pack.py",
                    "--input",
                    str(input_json),
                    "--out-dir",
                    str(out_dir),
                    "--include-acceptance-template",
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "PROPOSAL.md").exists())
            self.assertTrue((out_dir / "SOW.md").exists())
            self.assertTrue((out_dir / "ACCEPTANCE_CRITERIA.md").exists())
            self.assertTrue((out_dir / "MANIFEST.json").exists())

            proposal_text = (out_dir / "PROPOSAL.md").read_text(encoding="utf-8")
            self.assertIn("Client: Example Protocol A", proposal_text)

            sow_text = (out_dir / "SOW.md").read_text(encoding="utf-8")
            self.assertIn("Provider signatory: Cody Mitchell", sow_text)

    def test_deal_pack_fails_when_required_field_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            work_dir = Path(tmp_dir)
            input_data = json.loads(
                (ROOT / "strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            input_data["proposal"].pop("fee", None)

            input_path = work_dir / "bad-deal.json"
            input_path.write_text(json.dumps(input_data), encoding="utf-8")
            out_dir = work_dir / "deal-pack"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/deal_pack.py",
                    "--input",
                    str(input_path),
                    "--out-dir",
                    str(out_dir),
                ]
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required fields: fee", result.stderr)

    def test_pipeline_health_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "PIPELINE_HEALTH.md"
            pipeline_csv = ROOT / "strategy/assets/crm/PIPELINE_TEMPLATE.csv"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/pipeline_health.py",
                    "--pipeline",
                    str(pipeline_csv),
                    "--as-of",
                    "2026-03-01",
                    "--out",
                    str(out_path),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out_path.exists())
            report = out_path.read_text(encoding="utf-8")
            self.assertIn("# Pipeline Health Report", report)
            self.assertIn("Total score:", report)
            self.assertIn("Stage Distribution (Open Only)", report)

    def test_outbound_focus_generates_report_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_md = Path(tmp_dir) / "OUTBOUND_FOCUS.md"
            out_csv = Path(tmp_dir) / "OUTBOUND_FOCUS.csv"
            pipeline_csv = ROOT / "strategy/assets/crm/PIPELINE_TEMPLATE.csv"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/outbound_focus.py",
                    "--pipeline",
                    str(pipeline_csv),
                    "--as-of",
                    "2026-03-01",
                    "--out",
                    str(out_md),
                    "--csv-out",
                    str(out_csv),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out_md.exists())
            self.assertTrue(out_csv.exists())

            report = out_md.read_text(encoding="utf-8")
            self.assertIn("# Outbound Focus Plan", report)
            self.assertIn("Example Protocol A", report)
            self.assertIn("Example Fund B", report)
            self.assertNotIn("Example Protocol C", report)

            csv_text = out_csv.read_text(encoding="utf-8")
            self.assertIn("priority_score", csv_text)
            self.assertIn("Example Protocol A", csv_text)

    def test_outbound_focus_rejects_bad_as_of(self) -> None:
        result = run_cmd(
            [
                PYTHON,
                "scripts/outbound_focus.py",
                "--pipeline",
                "strategy/assets/crm/PIPELINE_TEMPLATE.csv",
                "--as-of",
                "2026-99-99",
            ]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid --as-of date", result.stdout)

    def test_commercial_review_package_without_deal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "commercial-package"

            result = run_cmd(
                [
                    "bash",
                    "scripts/commercial_review_package.sh",
                    "--pipeline",
                    "strategy/assets/crm/PIPELINE_TEMPLATE.csv",
                    "--kpi",
                    "strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv",
                    "--as-of",
                    "2026-03-01",
                    "--out-dir",
                    str(out_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "WEEKLY_DASHBOARD.md").exists())
            self.assertTrue((out_dir / "PIPELINE_HEALTH.md").exists())
            self.assertTrue((out_dir / "OUTBOUND_FOCUS.md").exists())
            self.assertTrue((out_dir / "OUTBOUND_FOCUS.csv").exists())
            self.assertTrue((out_dir / "MANIFEST.md").exists())
            self.assertTrue((out_dir / "SHA256SUMS").exists())
            self.assertFalse((out_dir / "deal-pack").exists())
            self.assertTrue(Path(f"{out_dir}.tar.gz").exists())

    def test_commercial_review_package_with_deal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "commercial-package"

            result = run_cmd(
                [
                    "bash",
                    "scripts/commercial_review_package.sh",
                    "--pipeline",
                    "strategy/assets/crm/PIPELINE_TEMPLATE.csv",
                    "--kpi",
                    "strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv",
                    "--deal-input",
                    "strategy/assets/contracts/DEAL_INPUT_TEMPLATE.json",
                    "--as-of",
                    "2026-03-01",
                    "--out-dir",
                    str(out_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "deal-pack/PROPOSAL.md").exists())
            self.assertTrue((out_dir / "deal-pack/SOW.md").exists())
            self.assertTrue((out_dir / "deal-pack/ACCEPTANCE_CRITERIA.md").exists())

    def test_commercial_review_package_with_portal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "commercial-package"

            result = run_cmd(
                [
                    "bash",
                    "scripts/commercial_review_package.sh",
                    "--pipeline",
                    "strategy/assets/crm/PIPELINE_TEMPLATE.csv",
                    "--kpi",
                    "strategy/assets/ops/KPI_TRACKER_TEMPLATE.csv",
                    "--portal-input",
                    "strategy/assets/portal/PORTAL_INPUT_TEMPLATE.json",
                    "--as-of",
                    "2026-03-01",
                    "--out-dir",
                    str(out_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "evidence-portal/INDEX.md").exists())
            self.assertTrue((out_dir / "evidence-portal/ARTIFACTS.md").exists())


if __name__ == "__main__":
    unittest.main()
