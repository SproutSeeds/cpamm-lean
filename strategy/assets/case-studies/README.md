# Case Study Assets

Use `CASE_STUDY_INPUT_TEMPLATE.json` as the structured input contract for sanitized case-study generation.

Generate a case-study package:

```bash
python3 scripts/case_study_pack.py \
  --input strategy/assets/case-studies/CASE_STUDY_INPUT_TEMPLATE.json
```

Default output path:

- `strategy/private/case-studies/<case_study_id>/`

Generated files:

- `CASE_STUDY.md`
- `CASE_STUDY_SUMMARY.json`
- `MANIFEST.json`
