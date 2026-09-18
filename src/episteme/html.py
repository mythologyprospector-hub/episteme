"""Static browser rendering for the read-only Episteme public instrument."""

from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any


def render_discovery_report_html(report: dict[str, Any]) -> str:
    """Render a discovery report as a self-contained, read-only HTML document."""
    finding_id = str(report["finding_id"])
    grounded = report.get("grounded_records", [])
    generated = report.get("generated_artifacts", [])
    lineage = report.get("lineage", {})
    trail = report.get("trail", {})

    def block(value: Any) -> str:
        return (
            '<pre class="data">'
            + html.escape(
                json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            )
            + "</pre>"
        )

    def artifact_list(entries: list[dict[str, Any]]) -> str:
        if not entries:
            return '<p class="empty">None in this trail.</p>'
        counts = Counter(str(entry.get("kind", "unknown")) for entry in entries)
        summary = "".join(
            f'<span class="tag">{html.escape(kind)}: {count}</span>'
            for kind, count in sorted(counts.items())
        )
        items = []
        for entry in entries:
            kind = html.escape(str(entry.get("kind", "unknown")))
            entry_id = html.escape(str(entry.get("id", "")))
            label = html.escape(
                str(entry.get("data", {}).get("title")
                    or entry.get("data", {}).get("statement")
                    or entry.get("data", {}).get("description")
                    or entry_id)
            )
            items.append(
                "<details><summary>"
                f"<strong>{kind}</strong> — {label}"
                "</summary>"
                f"{block(entry)}"
                "</details>"
            )
        return f'<div class="tags">{summary}</div>' + "".join(items)

    body = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Episteme discovery report</title>",
        """<style>
body{font-family:system-ui,sans-serif;line-height:1.45;max-width:1100px;margin:0 auto;padding:2rem;color:#222}
header{margin-bottom:2rem}h1{font-size:1.8rem;margin-bottom:.4rem}h2{margin-top:2.2rem}
.notice{padding:1rem;border:1px solid #bbb;border-radius:.4rem;background:#f7f7f7}
.summary{display:flex;gap:.7rem;flex-wrap:wrap;margin:1rem 0}.card{padding:.8rem 1rem;border:1px solid #ddd;border-radius:.4rem}
.tags{display:flex;gap:.4rem;flex-wrap:wrap;margin:.8rem 0}.tag{border:1px solid #ccc;border-radius:1rem;padding:.2rem .6rem;font-size:.9rem}
details{margin:.7rem 0;border:1px solid #ddd;border-radius:.4rem;padding:.7rem}.data{white-space:pre-wrap;overflow:auto;padding:1rem;border:1px solid #ddd;border-radius:.4rem;background:#fafafa}
.empty{color:#666}small{color:#555}
</style></head><body>""",
        f'<header><h1>Episteme discovery report</h1><p><strong>Finding:</strong> {html.escape(finding_id)}</p>',
        '<p class="notice"><strong>Read-only.</strong> Grounded records are evidence Episteme received or recorded; generated artifacts are Episteme-produced reasoning or planning material. This report does not adjudicate truth.</p>',
        f'<div class="summary"><div class="card"><strong>{len(grounded)}</strong><br>grounded records</div><div class="card"><strong>{len(generated)}</strong><br>generated artifacts</div><div class="card"><strong>{len(trail.get("entries", []))}</strong><br>trail entries</div></div></header>',
        "<section><h2>Grounded records</h2>",
        artifact_list(grounded),
        "</section>",
        "<section><h2>Generated artifacts</h2>",
        artifact_list(generated),
        "</section>",
        "<section><h2>Full trail</h2>",
        block(trail),
        "</section>",
        "<section><h2>Reproducible lineage</h2>",
        block(lineage),
        "</section>",
        "</body></html>",
    ]
    return "\n".join(body)


__all__ = ["render_discovery_report_html"]
