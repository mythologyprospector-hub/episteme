"""Static browser rendering for the read-only Episteme public instrument."""

from __future__ import annotations

import html
import json
from collections import Counter
from urllib.parse import urlencode
from typing import Any


def _instrument_css() -> str:
    return """<style>
:root{
  color-scheme:dark;
  --ink:#e8eef5;--muted:#91a2b5;--dim:#65778a;--panel:#111a24;
  --panel-2:#0d151e;--line:#243544;--accent:#67d6c4;
  --accent-2:#77a9ff;--warm:#e8bd72;--shadow:0 18px 55px rgba(0,0,0,.28)
}
*{box-sizing:border-box}
html{background:#081018}
body{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  line-height:1.55;max-width:1120px;margin:0 auto;padding:2.5rem 1.25rem 4rem;
  color:var(--ink);background:
  radial-gradient(circle at 12% 0%,rgba(103,214,196,.09),transparent 30rem),
  radial-gradient(circle at 90% 8%,rgba(119,169,255,.08),transparent 28rem)
}
header{margin-bottom:2.5rem}
.eyebrow{color:var(--accent);font-size:.78rem;font-weight:750;letter-spacing:.16em;text-transform:uppercase;margin:0 0 .55rem}
h1{font-size:clamp(2.2rem,6vw,4rem);line-height:1.02;letter-spacing:-.05em;margin:0 0 .75rem}
h2{font-size:1.2rem;letter-spacing:-.015em;margin:2.5rem 0 .8rem}
.subtitle{color:var(--muted);max-width:760px;margin:0}
.notice{
  margin-top:1.2rem;padding:1rem 1.1rem;border:1px solid #2c4554;border-radius:.7rem;
  background:linear-gradient(135deg,rgba(103,214,196,.08),rgba(119,169,255,.05));color:#cbd7e2;cursor:default
}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.8rem}
.card{
  display:block;text-decoration:none;color:inherit;padding:1.1rem 1.15rem;
  border:1px solid var(--line);border-radius:.75rem;background:linear-gradient(180deg,var(--panel),var(--panel-2));
  box-shadow:0 8px 24px rgba(0,0,0,.16);transition:border-color .15s,transform .15s
}
.card:hover{border-color:#416272;transform:translateY(-1px)}
.kind{color:var(--accent);font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.card h3{margin:.35rem 0 .4rem;font-size:1.05rem}
.card p{margin:0;color:var(--muted)}
.meta{margin-top:.8rem;color:var(--dim);font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;overflow-wrap:anywhere}
.empty{
  padding:1.2rem;border:1px dashed var(--line);border-radius:.7rem;color:var(--muted);
  background:rgba(17,26,36,.5)
}
footer{margin-top:3rem;color:var(--dim);font-size:.8rem;border-top:1px solid var(--line);padding-top:1rem}
@media (max-width:700px){body{padding:1.4rem .8rem 3rem}.grid{grid-template-columns:1fr}}
</style>"""


def render_observatory_html(discoveries: list[dict[str, Any]]) -> str:
    """Render the read-only human-facing entry point over existing discoveries."""
    cards = []
    for finding in discoveries:
        finding_id = html.escape(str(finding.get("id", "")))
        kind = html.escape(str(finding.get("kind", "discovery")))
        title = html.escape(str(finding.get("title") or "Untitled discovery"))
        description = html.escape(str(finding.get("description") or ""))
        created_at = str(finding.get("created_at", ""))
        query = urlencode({"created_at": created_at, "format": "html"})
        href = (
            "/api/v1/discoveries/"
            + finding_id
            + "/report?"
            + html.escape(query, quote=True)
        )
        cards.append(
            f'<a class="card" href="{href}">'
            f'<span class="kind">{kind}</span>'
            f'<h3>{title}</h3>'
            f'<p>{description}</p>'
            f'<div class="meta">Open discovery report · {html.escape(finding_id)}</div>'
            "</a>"
        )
    content = (
        "".join(cards)
        if cards
        else '<div class="empty">No discoveries have been recorded yet. The instrument is ready for its first finding.</div>'
    )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Episteme · Observatory</title>",
            _instrument_css(),
            "</head><body>",
            "<header>",
            '<p class="eyebrow">Scientific discovery instrument</p>',
            "<h1>Observatory</h1>",
            '<p class="subtitle">Start with a discovery. Follow what Episteme recorded, what it generated, and how the pieces connect.</p>',
            "<p class=\"notice\"><strong>Read-only.</strong> This is a window into Episteme's recorded state. Presentation does not decide what is true.</p>",
            "</header>",
            "<main>",
            "<h2>Discoveries</h2>",
            f'<div class="grid">{content}</div>',
            "</main>",
            "<footer>Episteme · read-only inspection · presentation never grants epistemic authority</footer>",
            "</body></html>",
        ]
    )


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
            return '<p class="empty">Nothing recorded in this trail.</p>'
        counts = Counter(str(entry.get("kind", "unknown")) for entry in entries)
        summary = "".join(
            f'<span class="tag">{html.escape(kind)} <b>{count}</b></span>'
            for kind, count in sorted(counts.items())
        )
        items = []
        for entry in entries:
            kind_value = str(entry.get("kind", "unknown"))
            kind = html.escape(kind_value)
            entry_id = html.escape(str(entry.get("id", "")))
            label = html.escape(
                str(
                    entry.get("data", {}).get("title")
                    or entry.get("data", {}).get("statement")
                    or entry.get("data", {}).get("description")
                    or entry_id
                )
            )
            data = entry.get("data", {})
            via = html.escape(str(entry.get("via", "")))
            method = html.escape(str(data.get("method", "")))
            rationale = html.escape(str(data.get("rationale", "")))
            context = []
            if via:
                context.append(f'<small><strong>Reached via</strong> · {via}</small>')
            if method:
                context.append(f'<small><strong>Method</strong> · {method}</small>')
            if rationale:
                context.append(f"<p><strong>Why this step exists:</strong> {rationale}</p>")
            items.append(
                f'<details>'
                "<summary>"
                f'<span class="kind">{kind}</span><span class="label">{label}</span>'
                "</summary>"
                + "".join(context)
                + block(entry)
                + "</details>"
            )
        return f'<div class="tags">{summary}</div>' + "".join(items)

    body = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Episteme · Discovery Report</title>",
        _instrument_css().replace(
            "</style>",
            """
.data{white-space:pre-wrap;overflow:auto;margin:1rem 0 0;padding:1rem;border:1px solid #1f2e3b;border-radius:.55rem;background:#080f16;color:#b8c8d8;font:12px/1.55 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}
.finding{margin-top:1.3rem;padding:.75rem 1rem;border:1px solid var(--line);border-radius:.7rem;background:rgba(17,26,36,.72);box-shadow:var(--shadow);overflow:auto}.finding code{color:var(--accent-2)}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin:1.1rem 0 0}.summary .card{padding:1rem 1.1rem;display:block;transform:none}.summary .card:hover{transform:none}.summary strong{display:block;font-size:1.65rem;color:var(--accent);line-height:1}.summary span{display:block;color:var(--muted);font-size:.82rem;margin-top:.4rem}
.tags{display:flex;gap:.45rem;flex-wrap:wrap;margin:.85rem 0}.tag{display:inline-flex;gap:.4rem;align-items:center;border:1px solid var(--line);border-radius:999px;padding:.25rem .65rem;color:#b8c7d5;background:#101b26;font-size:.8rem}.tag b{color:var(--accent)}
details{margin:.7rem 0;border:1px solid var(--line);border-radius:.7rem;padding:.8rem 1rem;background:linear-gradient(180deg,var(--panel),var(--panel-2));box-shadow:0 8px 24px rgba(0,0,0,.16)}details[open]{border-color:#35505d}
summary{cursor:pointer;display:flex;gap:.7rem;align-items:baseline;list-style:none}summary::-webkit-details-marker{display:none}summary:before{content:"›";color:var(--dim);font-size:1.2rem;line-height:1;transition:transform .15s}details[open] summary:before{transform:rotate(90deg);color:var(--accent)}
.summary .kind,.kind{flex:0 0 auto;color:var(--accent);font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}.label{font-weight:650}
small{color:var(--muted);display:block;margin:.65rem 0 .2rem;padding-left:1.45rem}details p{color:#c0cedb;padding-left:1.45rem}.empty{color:var(--dim);font-style:italic}
@media (max-width:700px){.summary{grid-template-columns:1fr}}
</style>""",
        ),
        "</head><body>",
        "<header>",
        '<p class="eyebrow">Scientific discovery instrument</p>',
        '<h1>Discovery report</h1>',
        '<p class="subtitle">An inspectable view of what Episteme recorded, what it generated, and how those pieces are connected.</p>',
        f'<div class="finding"><span>Finding</span> · <code>{html.escape(finding_id)}</code></div>',
        '<p class="notice"><strong>Read-only.</strong> Grounded records are evidence Episteme received or recorded; generated artifacts are Episteme-produced reasoning or planning material. This report does not adjudicate truth.</p>',
        f'<div class="summary"><div class="card"><strong>{len(grounded)}</strong><span>grounded records</span></div><div class="card"><strong>{len(generated)}</strong><span>generated artifacts</span></div><div class="card"><strong>{len(trail.get("entries", []))}</strong><span>trail entries</span></div></div>',
        "</header>",
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
        "<footer>Episteme · read-only inspection · presentation never grants epistemic authority</footer>",
        "</body></html>",
    ]
    return "\n".join(body)


__all__ = ["render_observatory_html", "render_discovery_report_html"]
