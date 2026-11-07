# gtm-account-research

<p>
<a href="https://github.com/DrAKULA12-lab/gtm-account-research/actions/workflows/ci.yml"><img src="https://github.com/DrAKULA12-lab/gtm-account-research/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="https://github.com/DrAKULA12-lab/gtm-account-research/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT"></a>
<img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" alt="Python 3.9+">
</p>

Open-source CLI that turns a company domain into a one-page account brief
for GTM and outbound teams. Public sources only. No API keys.

Built in the open so the GTM community can share signals and playbooks
instead of only consuming other people's tools.

## What you get

- Company overview (title, description, headline)
- Detected tech stack with categories (CRM, chat, analytics, payments...)
- Social links and GitHub activity, found automatically
- Hiring signals (Greenhouse, Lever, Ashby and more)
- Outreach angles from YAML playbooks anyone can edit
- Batch mode with a one-row-per-account CSV summary

## Install

    pip install git+https://github.com/DrAKULA12-lab/gtm-account-research.git

Or from source:

    git clone https://github.com/DrAKULA12-lab/gtm-account-research.git
    cd gtm-account-research
    pip install -e .

## Usage

    acr stripe.com
    acr stripe.com --github stripe
    acr stripe.com --json
    acr --file domains.txt --csv

domains.txt: one domain per line, optional GitHub name after a comma.

    hubspot.com,hubspot
    notion.so

Briefs are saved in the briefs/ folder. With `--csv`, briefs/summary.csv holds
one row per account (tech stack, hiring platform, GitHub stats, top angle, all angles),
ready to open in Excel or Google Sheets.

Set GITHUB_TOKEN to raise the GitHub API rate limit.

## Example output

    ## Suggested Outreach Angles
    - Careers page is live: check open roles as a growth signal.
    - Public pricing page: self-serve motion, lead with time-to-value.
    - Large open-source footprint at stripe.com: lead with developer experience and integrations.

## How it works

1. Collect: homepage HTML, key pages (careers, pricing...) and the GitHub API.
2. Detect: match technologies and hiring platforms using acr/data/*.yml.
3. Decide: apply the rules in acr/playbooks/*.yml to produce outreach angles.
4. Report: write a Markdown or JSON brief, and an optional CSV summary.

## Extend it without writing Python

- Add a technology: edit acr/data/tech.yml
- Add a hiring platform: edit acr/data/ats.yml
- Add outreach rules: add a file in acr/playbooks/ (see acr/playbooks/README.md)

Example tech entry:

    - name: ExampleCRM
      category: crm
      signatures: ["cdn.examplecrm.com", "examplecrm-tracker"]

Check your changes:

    acr --check-playbooks
    pytest

## Limits

Signals come from public homepage HTML and the GitHub API. Tools loaded through
a tag manager or after login will not appear. Treat gaps as hints to verify.

## Responsible use

Public pages only. Keep request volume low, follow each site's terms, and respect
privacy laws when contacting people.

## Roadmap

- [x] YAML playbooks and data files
- [x] CSV export for batch runs
- [ ] More technology and hiring platform signatures
- [ ] Optional AI summary and outreach draft per brief
- [ ] MCP server so AI agents can call acr as a tool

## Contributing

See CONTRIBUTING.md. The easiest first contribution is a YAML entry.

## License

MIT
