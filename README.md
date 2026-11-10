# gtm-account-research

<p>
<a href="https://github.com/DrAKULA12-lab/gtm-account-research/actions/workflows/ci.yml"><img src="https://github.com/DrAKULA12-lab/gtm-account-research/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="https://github.com/DrAKULA12-lab/gtm-account-research/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT"></a>
<img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+">
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
- An MCP server, so AI agents can call it as a tool

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

## Use it from AI agents (MCP)

acr also ships an MCP server, so an agent can research companies by calling it as a tool.

    claude mcp add acr -- acr-mcp
    acr-mcp --selftest linear.app

It only talks to public internet hosts and is read-only. Setup for other clients and the security model are in docs/mcp.md.

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
- [x] MCP server so AI agents can call acr as a tool

## Contributing

See CONTRIBUTING.md. The easiest first contribution is a YAML entry.

## License

MIT

## Use acr from AI agents (MCP)

acr includes an [MCP](https://modelcontextprotocol.io) server, so AI agents can call it as a tool. Install with `pip install "gtm-account-research[mcp]"` (Python 3.10 or newer).

**Tools**

| Tool | What it does |
|------|--------------|
| `research_account` | Builds a GTM account brief for one company domain |
| `research_accounts` | Builds briefs for up to 10 domains at once |
| `list_playbook_rules` | Lists the playbook rules acr uses |

**Connect it**

Claude Code:

~~~bash
claude mcp add acr -- python -m acr.mcp_server
~~~

Other MCP clients (Claude Desktop, Cursor, etc.) use the same command in their config:

~~~json
{
  "mcpServers": {
    "acr": {
      "command": "python",
      "args": ["-m", "acr.mcp_server"]
    }
  }
}
~~~

Then ask your agent: "Research stripe.com with acr."

**Security note:** page titles and descriptions come from third-party websites. acr labels them as data, so agents should never treat them as instructions.

## Cache

acr keeps fetched pages in `~/.cache/acr` for 24 hours, so repeat runs are fast and gentle on websites. Use `--no-cache` for fresh data, or set `ACR_NO_CACHE=1`. `ACR_CACHE_TTL` (in seconds) and `ACR_CACHE_DIR` change how long pages are kept and where.
