"""
apps/api/routers/analytics.py
Analytics read endpoints + a dashboard you can open on a phone.

ACCESS
------
Everything here is behind FINSIGHT_ANALYTICS_TOKEN. If the variable is unset the
endpoints return 503 rather than serving openly: these responses describe real
people's behaviour, the API is public, and "open unless someone remembers to
configure it" is how internal dashboards end up indexed.

The token is accepted as ?token= as well as a header, because the entire point
is opening it on a phone. A query token leaks into browser history and proxy
logs — acceptable for a personal dashboard over a demo round, not a pattern to
carry into anything larger.

WHY AN OVERVIEW ENDPOINT
------------------------
/analytics/session/{id} and /funnel/{id} answer "what did this one person do",
which requires collecting a session_id from every tester by hand. Nobody does
that. The question a demo round actually asks is "where do people fall out",
and nothing answered it: scripts/analytics_report.py reads the local database,
not production.
"""

from __future__ import annotations

import os

from analytics.metrics import (
    calculate_funnel,
    calculate_overview,
    calculate_session_summary,
)
from fastapi import APIRouter, Header, Query
from fastapi.responses import HTMLResponse, JSONResponse
from validation_gateway.health import health_tracker

from apps.api.ratelimit import explain_budget

router = APIRouter(prefix="/analytics")


def _configured_token() -> str:
    return os.environ.get("FINSIGHT_ANALYTICS_TOKEN", "").strip()


def _denied(token: str | None, header_token: str | None) -> JSONResponse | None:
    expected = _configured_token()
    if not expected:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "code": "ANALYTICS_TOKEN_NOT_SET",
                "message": (
                    "Set FINSIGHT_ANALYTICS_TOKEN to enable the analytics "
                    "endpoints. They stay closed until you do."
                ),
            },
        )
    supplied = (header_token or token or "").strip()
    # Length-independent comparison is overkill for a demo dashboard, but it
    # costs one import and removes the question.
    import hmac
    if not supplied or not hmac.compare_digest(supplied, expected):
        return JSONResponse(
            status_code=401,
            content={"status": "error", "code": "UNAUTHORIZED"},
        )
    return None


@router.get("/overview")
async def overview(
    token: str | None = Query(default=None),
    x_analytics_token: str | None = Header(default=None),
):
    denied = _denied(token, x_analytics_token)
    if denied:
        return denied
    return calculate_overview()


@router.get("/session/{session_id}")
async def session_summary(
    session_id: str,
    token: str | None = Query(default=None),
    x_analytics_token: str | None = Header(default=None),
):
    denied = _denied(token, x_analytics_token)
    if denied:
        return denied
    return calculate_session_summary(session_id)


@router.get("/funnel/{session_id}")
async def session_funnel(
    session_id: str,
    token: str | None = Query(default=None),
    x_analytics_token: str | None = Header(default=None),
):
    denied = _denied(token, x_analytics_token)
    if denied:
        return denied
    return calculate_funnel(session_id)


@router.get("/ai-health")
async def ai_health(
    token: str | None = Query(default=None),
    x_analytics_token: str | None = Header(default=None),
):
    denied = _denied(token, x_analytics_token)
    if denied:
        return denied
    return {**health_tracker.summary(), "daily_ai_budget": explain_budget.state()}


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    token: str | None = Query(default=None),
    x_analytics_token: str | None = Header(default=None),
):
    denied = _denied(token, x_analytics_token)
    if denied:
        return HTMLResponse(_ERROR_PAGE, status_code=denied.status_code)
    return HTMLResponse(_PAGE)


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------
#
# One hue for the bars and text tokens for everything else. The obvious design
# — green for accepted, red for rejected — fails a colour-vision check: those
# two brand steps sit ΔE 5.4 apart under deuteranopia, so a red-green reader
# would see two identical numbers. Counts are labelled instead, and colour
# carries no meaning it is the only carrier of.
#
# The funnel is a table with bars rather than a chart beside a table: at six
# ordered stages the label, the count and the length are the whole story.

_ERROR_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FinSight analytics</title>
<style>
  body{margin:0;min-height:100dvh;display:grid;place-items:center;
       background:#131313;color:#e5e2e1;
       font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
  div{max-width:32rem;padding:2rem;text-align:center}
  code{background:#2a2a2a;padding:.15em .4em;border-radius:4px;font-size:.9em}
</style></head>
<body><div>
  <p>No access.</p>
  <p style="color:#c6c6c6">Append <code>?token=…</code> — the value of
  <code>FINSIGHT_ANALYTICS_TOKEN</code>. If the variable is not set on the
  server, these endpoints stay closed.</p>
</div></body></html>
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#131313">
<meta name="color-scheme" content="dark">
<title>FinSight — funnel</title>
<style>
  :root{
    --bg:#131313; --surface:#201f1f; --track:#2a2a2a; --line:rgba(255,255,255,.06);
    --ink:#e5e2e1; --ink-2:#c6c6c6; --ink-3:#6b6b6b; --accent:#FF6B00;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
       padding:max(1rem,env(safe-area-inset-top)) 1rem 3rem}
  main{max-width:46rem;margin:0 auto}
  h1{font-size:1.05rem;letter-spacing:.02em;margin:0 0 .25rem;font-weight:700}
  .sub{color:var(--ink-3);font-size:.8rem;margin:0 0 1.5rem}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));
         gap:.6rem;margin-bottom:2rem}
  .tile{background:var(--surface);border:1px solid var(--line);
        border-radius:12px;padding:.9rem 1rem}
  .tile b{display:block;font-size:1.9rem;font-weight:800;letter-spacing:-.02em;
          font-variant-numeric:tabular-nums;line-height:1.1}
  .tile span{display:block;color:var(--ink-3);font-size:.68rem;
             text-transform:uppercase;letter-spacing:.09em;margin-top:.35rem}
  h2{font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;
     color:var(--ink-3);margin:0 0 .8rem;font-weight:600}
  .stage{margin-bottom:.55rem}
  .row{display:flex;align-items:baseline;gap:.6rem;
       font-size:.86rem;margin-bottom:.3rem}
  .row .name{flex:1;color:var(--ink-2)}
  .row .n{font-variant-numeric:tabular-nums;font-weight:700}
  .row .pct{color:var(--ink-3);font-variant-numeric:tabular-nums;
            font-size:.78rem;min-width:3.2rem;text-align:right}
  .bar{height:8px;background:var(--track);border-radius:4px;overflow:hidden}
  .bar i{display:block;height:100%;background:var(--accent);
         border-radius:4px;min-width:2px;transition:width .3s}
  .drop{display:inline-block;margin-left:.4rem;font-size:.66rem;
        text-transform:uppercase;letter-spacing:.08em;color:var(--accent);
        border:1px solid var(--accent);border-radius:999px;padding:0 .45em}
  .empty{background:var(--surface);border:1px solid var(--line);
         border-radius:12px;padding:1.5rem;color:var(--ink-2);font-size:.9rem}
  footer{margin-top:2rem;color:var(--ink-3);font-size:.72rem}
  a{color:var(--ink-2)}
</style>
</head>
<body>
<main>
  <h1>FinSight — funnel</h1>
  <p class="sub" id="meta">loading…</p>
  <div class="tiles" id="tiles"></div>
  <h2>Where people fall out</h2>
  <div id="stages"></div>
  <footer id="foot"></footer>
</main>
<script>
const token = new URLSearchParams(location.search).get("token") || "";
const pct = v => v === null || v === undefined ? "—" : Math.round(v * 100) + "%";

function tile(value, label) {
  return `<div class="tile"><b>${value}</b><span>${label}</span></div>`;
}

function stage(s, max, isDrop) {
  const width = max ? (s.sessions / max) * 100 : 0;
  return `<div class="stage">
    <div class="row">
      <span class="name">${s.label}${isDrop ? '<span class="drop">biggest drop</span>' : ""}</span>
      <span class="n">${s.sessions}</span>
      <span class="pct">${pct(s.conversion_from_previous)}</span>
    </div>
    <div class="bar" title="${s.sessions} sessions · ${pct(s.share_of_all)} of all">
      <i style="width:${width}%"></i>
    </div>
  </div>`;
}

fetch("/analytics/overview?token=" + encodeURIComponent(token))
  .then(r => r.ok ? r.json() : Promise.reject(r.status))
  .then(d => {
    document.getElementById("meta").textContent =
      d.sessions === 0 ? "no sessions yet"
      : `${d.sessions} sessions · ${d.events} events · since ${(d.first_event_at || "").slice(0, 10)}`;

    document.getElementById("tiles").innerHTML = [
      tile(d.sessions, "sessions"),
      tile(d.decisions, "decisions"),
      tile(pct(d.dlcr), "loop completed"),
      tile(pct(d.acceptance_rate), "accepted"),
    ].join("");

    const max = Math.max(...d.stages.map(s => s.sessions), 0);
    const drop = d.biggest_drop && d.biggest_drop.label;
    document.getElementById("stages").innerHTML = d.sessions
      ? d.stages.map(s => stage(s, max, s.label === drop)).join("")
      : '<div class="empty">Nothing yet. The first person to open the app will show up here.</div>';

    document.getElementById("foot").innerHTML =
      `accepted ${d.accepted} · rejected ${d.rejected} · scenarios opened ${d.scenarios_opened}<br>
       percentages are conversion from the previous stage · raw JSON at
       <a href="/analytics/overview?token=${encodeURIComponent(token)}">/analytics/overview</a>`;
  })
  .catch(e => {
    document.getElementById("meta").textContent =
      e === 401 ? "wrong token" : e === 503 ? "FINSIGHT_ANALYTICS_TOKEN is not set on the server" : "failed to load (" + e + ")";
  });
</script>
</body>
</html>
"""
