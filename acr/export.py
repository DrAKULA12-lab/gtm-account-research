"""CSV export: one summary row per researched account."""

import csv
from pathlib import Path

COLUMNS = [
    "domain",
    "status",
    "error",
    "title",
    "tech_stack",
    "tech_categories",
    "hiring_platform",
    "pages_found",
    "github_repos",
    "github_followers",
    "github_last_push",
    "angle_count",
    "top_angle",
    "all_angles",
    "date",
]

# Spreadsheet apps run cells that start with these characters as formulas.
# Text comes from third-party websites, so neutralize it before writing.
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """Return value as text that a spreadsheet will not execute as a formula."""
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if text.startswith(_FORMULA_START):
        text = "'" + text
    return text


def to_row(d):
    """Flatten one research result into a dict keyed by COLUMNS."""
    site = d["site"]
    gh = d.get("github")
    row = dict.fromkeys(COLUMNS, "")
    row["domain"] = d["domain"]
    row["date"] = d["date"]

    if "error" in site:
        row["status"] = "error"
        row["error"] = site["error"]
        return {k: safe_cell(v) for k, v in row.items()}

    row["status"] = "ok"
    row["title"] = site["title"]
    row["tech_stack"] = ", ".join(site["stack"])
    row["tech_categories"] = ", ".join(site.get("categories", []))
    row["hiring_platform"] = ", ".join(site["ats"])
    row["pages_found"] = ", ".join(p for p, ok in site["pages"].items() if ok)
    if gh and "error" not in gh:
        row["github_repos"] = gh["public_repos"]
        row["github_followers"] = gh["followers"]
        row["github_last_push"] = gh["last_push"] or ""
    angles = d["angles"]
    row["angle_count"] = len(angles)
    row["top_angle"] = angles[0] if angles else ""
    row["all_angles"] = " | ".join(angles)
    return {k: safe_cell(v) for k, v in row.items()}


def write_csv(results, path):
    """Write a summary CSV (UTF-8 with BOM so Excel reads accents correctly)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for d in results:
            writer.writerow(to_row(d))
    return path
