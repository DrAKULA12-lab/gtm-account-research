# Use acr from AI agents (MCP)

`acr-mcp` is a Model Context Protocol server. It lets an AI agent (Claude, or any MCP
client) research a company by calling acr as a tool, instead of you running commands.

## Tools

| Tool | What it does |
|---|---|
| `research_account` | One-page brief for a company domain. `format` is `markdown` (default) or `json`. |
| `research_accounts` | Summary rows for up to 10 domains, to compare or shortlist accounts. |
| `list_playbook_rules` | The YAML rules behind the outreach angles, so the agent can explain them. |

All three are read-only. They make live requests to public websites and the GitHub API.

## Install

    pip install git+https://github.com/DrAKULA12-lab/gtm-account-research.git

This installs two commands: `acr` and `acr-mcp`. Check the server works:

    acr-mcp --selftest
    acr-mcp --selftest linear.app

## Connect it

Claude Code:

    claude mcp add acr -- acr-mcp

Claude Desktop and other clients: add this to the client's MCP config.

    {
      "mcpServers": {
        "acr": { "command": "acr-mcp" }
      }
    }

Desktop apps often do not see your shell PATH. If the client cannot start the server,
run `which acr-mcp` and put the full path in `"command"`.

Optional: set `ACR_PLAYBOOKS` to a playbook file or folder to use your own rules.
Set `GITHUB_TOKEN` to raise the GitHub rate limit.

## Try it

Ask your agent:

- "Research linear.app and tell me the best outreach angle."
- "Compare stripe.com, notion.so and vercel.com. Which one is hiring through Greenhouse?"
- "Why did you suggest that angle? List the playbook rules."

## Security model

An agent can be steered by text it reads, so the server is built to be safe to expose:

- **Public hosts only.** Domains are resolved first, and anything that is not a public
  internet address (localhost, private ranges, link-local such as 169.254.169.254,
  internal names) is refused. Credentials and custom ports in URLs are refused.
- **Redirects are checked.** A public site that redirects to an internal address is stopped
  before the redirect is followed.
- **Read-only.** No tool writes files, runs commands or reads local paths.
- **Untrusted text is labeled.** Website text in results is truncated and marked as data,
  not instructions, to reduce prompt injection.
- **Bounded.** Batches are limited to 10 domains and a crashing tool never stops the server.

Known limits: DNS can change between the check and the request (DNS rebinding), and the
server has no built-in rate limiting. Run it only for agents you trust with web access,
and keep request volume polite.

## How it is built

`acr/mcp_server.py` implements the protocol over stdio with the standard library only
(newline-delimited JSON-RPC 2.0), so it installs wherever acr does, including Termux.
`acr/safety.py` holds the network checks, and `acr/fetch.py` applies them to every request.
