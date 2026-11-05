# gtm-account-research

Open-source CLI that turns a company domain into a one-page account brief
for GTM and outbound teams. Public sources only, no API keys required.

## What you get

- Company overview (title, description, headline)
- Detected tech stack (CRM, chat, analytics, frameworks)
- Social links and GitHub activity (auto-detected)
- Hiring signals (Greenhouse, Lever, Ashby and more)
- Suggested outreach angles

## Install

    pip install -r requirements.txt

## Usage

    python acr.py stripe.com
    python acr.py stripe.com --github stripe
    python acr.py stripe.com --json
    python acr.py --file domains.txt

domains.txt format, one per line, optional GitHub name after a comma:

    hubspot.com,hubspot
    notion.so

Briefs are saved in the briefs/ folder.
Set GITHUB_TOKEN to raise the GitHub API rate limit.

## Limits

Signals come from the public homepage HTML and the GitHub API.
Tools loaded through a tag manager or after login will not appear.
Treat gaps as hints to verify, not facts.

## Roadmap

- playbooks/ folder with YAML signal rules anyone can contribute
- Optional AI summary of each brief
- CSV export for batch runs
- Job count and role categories

## Contributing

Add a tech signature to TECH, an ATS to ATS, or an outreach rule.
Small PRs are welcome.

## Responsible use

Public pages only. Be polite with request volume, follow each site's terms,
and respect privacy laws when contacting people.

## License

MIT
