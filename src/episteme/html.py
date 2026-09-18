"""Static browser rendering for the read-only Episteme public instrument."""

from __future__ import annotations

import html
import json
from typing import Any


def render_discovery_report_html(report: dict[str, Any]) -> str:
    """Render a discovery report as a self-contained, read-only HTML document."""
    title = f"Episteme discovery report — {report['finding_id']}"
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

    sections = [
        ("Grounded records", grounded),
        ("Generated artifacts", generated),
        ("Full trail", trail),
        ("Reproducible lineage", lineage),
    ]
    body = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(title)}</title>",
        """<style>
body{font-family:system-ui,sans-serif;line-height:1.45;max-width:1100px;margin:0 auto;padding:2rem;color:#222}
header{margin-bottom:2rem} h1{font-size:1.7rem} h2{margin-top:2rem}
.notice{padding:1rem;border:1px solid #bbb;border-radius:.4rem;background:#f7f7f7}
.data{white-space:pre-wrap;overflow:auto;padding:1rem;border:1px solid #ddd;border-radius:.4rem;background:#fafafa}
small{color:#555}
</style></head><body>""",
        f"<header><h1>Episteme discovery report</h1><p><strong>Finding:</strong> {html.escape(str(report['finding_id']))}</p>",
        '<p class="notice">Read-only presentation. Grounded records are separated from generated artifacts. This page does not adjudicate truth.</p></header>',
    ]
    for heading, value in sections:
        body.append(f"<section><h2>{html.escape(heading)}</h2>")
        body.append(block(value))
        body.append("</section>")
    body.extend(["</body></html>"])
    return "\n".join(body)


__all__ = ["render_discovery_report_html"]
