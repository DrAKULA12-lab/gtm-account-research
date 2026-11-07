"""Command-line interface."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from acr import __version__
from acr.core import research
from acr.export import write_csv
from acr.playbooks import DEFAULT_PLAYBOOKS, load_playbooks
from acr.report import save


def parse_file(path):
    """Read 'domain' or 'domain,github' lines, skipping blanks and # comments."""
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dom, _, gh = line.partition(",")
        items.append((dom.strip(), gh.strip() or None))
    return items


def build_parser():
    ap = argparse.ArgumentParser(prog="acr", description="GTM account research brief")
    ap.add_argument("domain", nargs="?", help="e.g. stripe.com")
    ap.add_argument("--github", help="GitHub org/user (auto-detected if omitted)")
    ap.add_argument("--file", help="text file, one 'domain' or 'domain,github' per line")
    ap.add_argument("--json", action="store_true", help="write JSON instead of Markdown")
    ap.add_argument(
        "--csv", action="store_true", help="also write one summary row per domain to summary.csv"
    )
    ap.add_argument("--out", default="briefs", help="output folder")
    ap.add_argument(
        "--playbooks",
        default=str(DEFAULT_PLAYBOOKS),
        help="playbook file or folder (default: the built-in playbooks)",
    )
    ap.add_argument(
        "--check-playbooks", action="store_true", help="validate playbook files and exit"
    )
    ap.add_argument("--version", action="version", version=f"acr {__version__}")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)

    rules, errors = load_playbooks(args.playbooks)

    if args.check_playbooks:
        for e in errors:
            print(f"[ERR] {e}")
        print(f"[+] {len(rules)} valid rule(s) loaded from {args.playbooks}")
        sys.exit(1 if errors else 0)

    for e in errors:
        print(f"[warn] {e}", file=sys.stderr)

    targets = []
    if args.file:
        if not Path(args.file).exists():
            ap.error(f"file not found: {args.file}")
        targets = parse_file(args.file)
    if args.domain:
        targets.insert(0, (args.domain, args.github))
    if not targets:
        ap.error("give a domain or --file")

    print(f"[*] Researching {len(targets)} account(s), {len(rules)} playbook rule(s) ...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(lambda t: research(t[0], t[1], rules), targets))

    for d in results:
        path, content = save(d, args.out, args.json)
        if len(results) == 1 and not args.csv:
            print(content)
        status = "ERR" if "error" in d["site"] else "OK"
        print(f"[{status}] {d['domain']} -> {path}")

    if args.csv:
        csv_path = write_csv(results, Path(args.out) / "summary.csv")
        print(f"[+] Summary of {len(results)} account(s) -> {csv_path}")


if __name__ == "__main__":
    main()
