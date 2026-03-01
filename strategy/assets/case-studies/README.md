# Case Study Assets

Use `CASE_STUDY_INPUT_TEMPLATE.json` as the structured input contract for sanitized case-study generation.

Generate a case-study package:

```bash
python3 scripts/case_study_pack.py \
  --input strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json
```

Generate multiple case-study packages into one root:

```bash
python3 scripts/case_study_pack.py \
  --input strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json \
  --out-root artifacts/case-studies
```

Generate a cross-case-study index and rollup:

```bash
python3 scripts/case_study_index.py \
  --inputs strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json \
  --out reports/CASE_STUDIES_INDEX.md \
  --json-out reports/CASE_STUDIES_ROLLUP.json
```

Or resolve from glob:

```bash
python3 scripts/case_study_index.py \
  --input-glob "strategy/private/case-studies/*.json" \
  --out reports/CASE_STUDIES_INDEX.md \
  --json-out reports/CASE_STUDIES_ROLLUP.json
```

Default output path:

- `strategy/private/case-studies/<case_study_id>/`

Generated files:

- `CASE_STUDY.md`
- `CASE_STUDY_SUMMARY.json`
- `MANIFEST.json`

Index outputs:

- `CASE_STUDIES_INDEX.md`
- `CASE_STUDIES_ROLLUP.json`
