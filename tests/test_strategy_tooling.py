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
            case_index = tmp / "CASE_STUDIES_INDEX.md"
            case_rollup = tmp / "CASE_STUDIES_ROLLUP.json"
            commercial_src.mkdir(parents=True, exist_ok=True)
            review_src.mkdir(parents=True, exist_ok=True)

            (commercial_src / "MANIFEST.md").write_text("# Commercial Package\n", encoding="utf-8")
            (commercial_src / "SHA256SUMS").write_text("abc  file.txt\n", encoding="utf-8")
            (commercial_src / "file.txt").write_text("ok\n", encoding="utf-8")
            (review_src / "MANIFEST.md").write_text("# Review Package\n", encoding="utf-8")
            (review_src / "SHA256SUMS").write_text("def  report.log\n", encoding="utf-8")
            (review_src / "report.log").write_text("ok\n", encoding="utf-8")
            case_index.write_text("# Case Studies Index\n", encoding="utf-8")
            case_rollup.write_text("{\"rollup\": {\"case_study_count\": 1}}\n", encoding="utf-8")

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
                    "--case-studies-index",
                    str(case_index),
                    "--case-studies-rollup",
                    str(case_rollup),
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
            self.assertTrue((portal_out / "artifacts/case-studies/CASE_STUDIES_INDEX.md").exists())
            self.assertTrue((portal_out / "artifacts/case-studies/CASE_STUDIES_ROLLUP.json").exists())

            index_text = (portal_out / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("Engagement ID: example-protocol-a-2026q1", index_text)

            artifacts_text = (portal_out / "ARTIFACTS.md").read_text(encoding="utf-8")
            self.assertIn("Commercial Package", artifacts_text)
            self.assertIn("Technical Review Package", artifacts_text)
            self.assertIn("Case Studies Index", artifacts_text)
            self.assertIn("Case Studies Rollup", artifacts_text)

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
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_path = Path(tmp_dir) / "kpi-result.json"
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
                    "--result-json-out",
                    str(result_path),
                    "--dry-run",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["assignees"], ["alice", "bob-1"])
            self.assertTrue(result_path.exists())
            meta = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(meta["status"], "dry_run")
            self.assertEqual(meta["kind"], "kpi")
            self.assertEqual(meta["issue_number"], None)

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
                "--case-study-input",
                "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json",
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

    def test_validate_strategy_data_rejects_bad_case_study_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_case_study = Path(tmp_dir) / "CASE_STUDY_BAD.json"
            payload = json.loads(
                (ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            payload["case_study_id"] = "bad id with spaces"
            bad_case_study.write_text(json.dumps(payload), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/validate_strategy_data.py",
                    "--case-study-input",
                    str(bad_case_study),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("case_study_id must be slug-like", result.stdout)

    def test_case_study_pack_generates_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "case-study"
            input_json = ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_pack.py",
                    "--input",
                    str(input_json),
                    "--out-dir",
                    str(out_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "CASE_STUDY.md").exists())
            self.assertTrue((out_dir / "CASE_STUDY_SUMMARY.json").exists())
            self.assertTrue((out_dir / "MANIFEST.json").exists())

            text = (out_dir / "CASE_STUDY.md").read_text(encoding="utf-8")
            self.assertIn("AMM Launch Readiness", text)
            self.assertIn("Measurable Outcomes", text)

    def test_case_study_pack_generates_under_out_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_root = Path(tmp_dir) / "case-studies"
            input_json = ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_pack.py",
                    "--input",
                    str(input_json),
                    "--out-root",
                    str(out_root),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            case_dir = out_root / "amm-launch-readiness-2026q1"
            self.assertTrue((case_dir / "CASE_STUDY.md").exists())
            self.assertTrue((case_dir / "CASE_STUDY_SUMMARY.json").exists())
            self.assertTrue((case_dir / "MANIFEST.json").exists())

    def test_case_study_pack_rejects_bad_case_study_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_input = Path(tmp_dir) / "bad-case-study.json"
            payload = json.loads(
                (ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            payload["case_study_id"] = "bad id"
            bad_input.write_text(json.dumps(payload), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_pack.py",
                    "--input",
                    str(bad_input),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("case_study_id must be slug-like", result.stdout)

    def test_case_study_index_generates_rollup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            work = Path(tmp_dir)
            input_a = work / "case-a.json"
            input_b = work / "case-b.json"
            out_md = work / "CASE_STUDIES_INDEX.md"
            out_json = work / "CASE_STUDIES_ROLLUP.json"

            payload = json.loads(
                (ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            input_a.write_text(json.dumps(payload), encoding="utf-8")

            payload_b = dict(payload)
            payload_b["case_study_id"] = "amm-launch-readiness-2026q2"
            payload_b["published_date"] = "2026-04-01"
            payload_b["metrics"] = dict(payload["metrics"])
            payload_b["metrics"]["critical_findings_prevented"] = 5
            payload_b["metrics"]["proof_obligations_closed"] = 9
            input_b.write_text(json.dumps(payload_b), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_index.py",
                    "--inputs",
                    str(input_a),
                    str(input_b),
                    "--out",
                    str(out_md),
                    "--json-out",
                    str(out_json),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out_md.exists())
            self.assertTrue(out_json.exists())
            self.assertIn("# Case Studies Index", out_md.read_text(encoding="utf-8"))
            self.assertIn("amm-launch-readiness-2026q2", out_md.read_text(encoding="utf-8"))

            rollup = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(rollup["rollup"]["case_study_count"], 2)

    def test_case_study_index_rejects_missing_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_input = Path(tmp_dir) / "bad-case-study.json"
            payload = json.loads(
                (ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            payload["metrics"].pop("proof_obligations_closed", None)
            bad_input.write_text(json.dumps(payload), encoding="utf-8")

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_index.py",
                    "--inputs",
                    str(bad_input),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("metrics missing required fields", result.stdout)

    def test_case_study_index_supports_input_glob(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            work = Path(tmp_dir)
            input_a = work / "a.json"
            input_b = work / "b.json"
            payload = json.loads(
                (ROOT / "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json").read_text(encoding="utf-8")
            )
            input_a.write_text(json.dumps(payload), encoding="utf-8")
            payload_b = dict(payload)
            payload_b["case_study_id"] = "amm-launch-readiness-2026q3"
            payload_b["published_date"] = "2026-05-01"
            input_b.write_text(json.dumps(payload_b), encoding="utf-8")

            out_md = work / "INDEX.md"
            out_json = work / "ROLLUP.json"
            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_index.py",
                    "--input-glob",
                    str(work / "*.json"),
                    "--out",
                    str(out_md),
                    "--json-out",
                    str(out_json),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out_md.exists())
            self.assertTrue(out_json.exists())
            rollup = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(rollup["rollup"]["case_study_count"], 2)

    def test_case_study_portal_generates_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            work = Path(tmp_dir)
            case_root = work / "case-studies"
            case_dir = case_root / "amm-launch-readiness-2026q1"
            case_dir.mkdir(parents=True, exist_ok=True)
            (case_dir / "CASE_STUDY.md").write_text("# Case Study\n", encoding="utf-8")

            index_md = work / "CASE_STUDIES_INDEX.md"
            index_md.write_text("# Case Studies Index\n", encoding="utf-8")
            rollup_json = work / "CASE_STUDIES_ROLLUP.json"
            rollup_json.write_text(
                json.dumps(
                    {
                        "rollup": {
                            "case_study_count": 1,
                            "published_window": {"start": "2026-03-01", "end": "2026-03-01"},
                            "totals": {
                                "critical_findings_prevented": 3,
                                "proof_obligations_closed": 7,
                                "regression_escape_reduction": 2,
                            },
                            "averages": {
                                "ci_gate_improvement_pct_points": 36,
                                "time_to_green_reduction_days": 7,
                            },
                            "by_segment": {"protocol": 1},
                        },
                        "entries": [
                            {
                                "case_study_id": "amm-launch-readiness-2026q1",
                                "title": "AMM Launch Readiness",
                                "published_date": "2026-03-01",
                                "client_segment": "protocol",
                                "engagement_type": "verification_sprint",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out_dir = work / "case-study-portal"
            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_portal.py",
                    "--index-md",
                    str(index_md),
                    "--rollup-json",
                    str(rollup_json),
                    "--case-studies-dir",
                    str(case_root),
                    "--out-dir",
                    str(out_dir),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "INDEX.md").exists())
            self.assertTrue((out_dir / "MANIFEST.json").exists())
            self.assertTrue((out_dir / "CASE_STUDIES_INDEX.md").exists())
            self.assertTrue((out_dir / "CASE_STUDIES_ROLLUP.json").exists())
            self.assertTrue((out_dir / "case-studies/amm-launch-readiness-2026q1/CASE_STUDY.md").exists())
            text = (out_dir / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("Case Study Portal", text)
            self.assertIn("amm-launch-readiness-2026q1", text)
            self.assertIn("case-studies/amm-launch-readiness-2026q1/CASE_STUDY.md", text)

    def test_case_study_portal_rejects_missing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            work = Path(tmp_dir)
            index_md = work / "CASE_STUDIES_INDEX.md"
            index_md.write_text("# Index\n", encoding="utf-8")
            bad_rollup = work / "BAD_ROLLUP.json"
            bad_rollup.write_text(json.dumps({"rollup": {}}), encoding="utf-8")
            result = run_cmd(
                [
                    PYTHON,
                    "scripts/case_study_portal.py",
                    "--index-md",
                    str(index_md),
                    "--rollup-json",
                    str(bad_rollup),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing 'entries' list", result.stdout)

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

    def test_outbound_sla_gate_passes_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_md = Path(tmp_dir) / "OUTBOUND_SLA.md"
            out_json = Path(tmp_dir) / "OUTBOUND_SLA.json"

            result = run_cmd(
                [
                    PYTHON,
                    "scripts/outbound_sla_gate.py",
                    "--pipeline",
                    "strategy/assets/crm/PIPELINE_TEMPLATE.csv",
                    "--as-of",
                    "2026-03-01",
                    "--out",
                    str(out_md),
                    "--json-out",
                    str(out_json),
                    "--strict",
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(out_md.exists())
            self.assertTrue(out_json.exists())

            md = out_md.read_text(encoding="utf-8")
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("# Outbound SLA Gate", md)
            self.assertEqual(payload["status"], "pass")

    def test_outbound_sla_gate_strict_fails_on_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_pipeline = Path(tmp_dir) / "PIPELINE_BAD.csv"
            bad_pipeline.write_text(
                (
                    "account_name,segment,contact_name,contact_role,contact_email,status,stage,deal_type,"
                    "acv_usd,probability_pct,expected_close_date,owner,next_action,next_action_date,last_touch_date,notes\n"
                    "Bad Protocol,protocol,Jane Doe,CTO,jane@example.org,open,discovery,sprint,50000,50,2026-06-01,"
                    "founder,Send follow-up,2026-01-01,2026-01-01,stale + overdue\n"
                ),
                encoding="utf-8",
            )
            out_json = Path(tmp_dir) / "OUTBOUND_SLA.json"
            result = run_cmd(
                [
                    PYTHON,
                    "scripts/outbound_sla_gate.py",
                    "--pipeline",
                    str(bad_pipeline),
                    "--as-of",
                    "2026-03-01",
                    "--json-out",
                    str(out_json),
                    "--max-overdue-ratio",
                    "0.00",
                    "--strict",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SLA breaches detected", result.stdout)
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "fail")

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
            self.assertTrue((out_dir / "OUTBOUND_SLA.md").exists())
            self.assertTrue((out_dir / "OUTBOUND_SLA.json").exists())
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

    def test_commercial_review_package_with_case_study(self) -> None:
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
                    "--case-study-input",
                    "strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json",
                    "--as-of",
                    "2026-03-01",
                    "--out-dir",
                    str(out_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "case-study/CASE_STUDY.md").exists())
            self.assertTrue((out_dir / "case-study/CASE_STUDY_SUMMARY.json").exists())
            self.assertTrue((out_dir / "CASE_STUDIES_INDEX.md").exists())
            self.assertTrue((out_dir / "CASE_STUDIES_ROLLUP.json").exists())


if __name__ == "__main__":
    unittest.main()
