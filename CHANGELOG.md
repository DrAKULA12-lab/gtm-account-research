# Changelog

## 0.5.0

- `--csv` writes one summary row per account to `summary.csv` (works with `--file` batches)
- CSV cells that start with `=`, `+`, `-` or `@` are neutralized, so data scraped from websites
  cannot run as a spreadsheet formula
- UTF-8 with BOM, so Excel shows accents and Arabic correctly

## 0.4.0

- Restructured as a Python package with an `acr` command
- Technology and hiring platform signatures moved to YAML (acr/data/)
- Tech categories, with has_category / lacks_category playbook conditions
- Tests, CI, contributor docs and GitHub templates
- Fix: links to domains such as dropbox.com were detected as an X profile

## 0.3.0

- YAML playbook engine and --check-playbooks

## 0.2.0

- Auto-detect GitHub org, hiring platform detection, --json, --file batch mode
- Soft-404 page detection and clearer outreach angles

## 0.1.0

- First account research brief
