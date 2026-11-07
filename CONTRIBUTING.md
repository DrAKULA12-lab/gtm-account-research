# Contributing

Thanks for helping build this in the open. Small contributions are welcome.

## Easiest ways to contribute (no Python)

- Add a technology to acr/data/tech.yml
- Add a hiring platform to acr/data/ats.yml
- Add a playbook in acr/playbooks/ for your vertical (fintech, ecommerce, security...)

Include one real domain where your change works, in the pull request description.

## Development setup

    git clone https://github.com/DrAKULA12-lab/gtm-account-research.git
    cd gtm-account-research
    pip install -e ".[dev]"

## Before opening a pull request

    ruff check .
    pytest
    acr --check-playbooks

## Project layout

    acr/analyze.py      fetch homepage, detect stack, socials, pages, hiring
    acr/github.py       GitHub API lookups
    acr/playbooks.py    load and run YAML rules
    acr/core.py         research one account end to end
    acr/report.py       Markdown and JSON output
    acr/cli.py          command line interface
    acr/export.py       CSV summary export
    acr/mcp_server.py   MCP server (stdio) so AI agents can call acr
    acr/safety.py       public-host checks used by the MCP server
    acr/data/           technology and hiring platform signatures (YAML)
    acr/playbooks/      built-in playbooks (YAML)
    tests/              offline tests, no network needed

## Adding a new data source

Create a module in acr/ that returns a plain dict, call it from acr/core.py,
add its fields to the result, render them in acr/report.py, and add offline tests
that mock the network.

## Guidelines

- Tests must not use the network. Mock acr.analyze.get or acr.fetch.get.
- Keep signatures lowercase. A test enforces it.
- Fetch pages with acr.fetch.get, never requests directly, so the MCP server's
  network guard applies to every request.
- Be kind and constructive in issues and reviews.
