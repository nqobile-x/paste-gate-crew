import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg  # type: ignore[assignment]

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from paste_gate_crew.crew import PasteGateCrew

VAULT_DIR = Path("obsidian_reports")


@asynccontextmanager
async def lifespan(app: FastAPI):
    VAULT_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="Paste Gate API", version="2.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class ScrubRequest(BaseModel):
    text: str


class ScrubResponse(BaseModel):
    scrubbed_text: str
    report: str
    elapsed_ms: int
    risk_level: str
    entities_found: int
    session_key: str


def _risk_from_report(report: str) -> tuple[str, int]:
    lower = report.lower()
    count = lower.count("[")
    if "high" in lower:
        return "high", count
    if "medium" in lower:
        return "medium", count
    return "low", count


@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!doctype html><html><head><meta charset="utf-8">
    <title>Paste Gate API</title>
    <style>body{font-family:system-ui,sans-serif;background:#0e0c0a;color:#e8e0d0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
    .card{text-align:center;padding:40px;border:1px solid #2e2a24;border-radius:16px;background:#181410;}
    h1{margin:0 0 8px;font-size:1.6rem;color:#c9a96e;}span{font-size:.85rem;color:#7a6e60;}
    a{color:#c9a96e;text-decoration:none;margin:0 12px;font-size:.9rem;}a:hover{text-decoration:underline;}</style>
    </head><body><div class="card">
    <h1>🛡 Paste Gate API</h1>
    <span>v2.4.0 — running</span><br><br>
    <a href="/health">/health</a><a href="/docs">/docs</a>
    </div></body></html>"""


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.4.0"}


@app.post("/scrub", response_model=ScrubResponse)
async def scrub(req: ScrubRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")

    t0 = time.monotonic()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: PasteGateCrew().crew().kickoff(
            inputs={"raw_text": req.text, "scrubbed_text": ""}
        ),
    )

    elapsed = int((time.monotonic() - t0) * 1000)
    report_str = str(result)
    risk, entities = _risk_from_report(report_str)

    # Auto-save report
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    import random, string
    key = "#" + "".join(random.choices(string.digits, k=4)) + "-" + "".join(random.choices(string.ascii_uppercase, k=2)) + "".join(random.choices(string.digits, k=2))
    report_path = VAULT_DIR / f"redaction-{ts}.md"
    report_path.write_text(
        f"---\ndate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\ntags: [paste-gate, redaction]\n---\n\n"
        f"## Input\n\n```\n{req.text}\n```\n\n---\n\n{report_str}",
        encoding="utf-8",
    )

    # Extract scrubbed text from result (first task output)
    tasks_output = getattr(result, "tasks_output", [])
    scrubbed = tasks_output[0].raw if tasks_output else req.text

    return ScrubResponse(
        scrubbed_text=scrubbed,
        report=report_str,
        elapsed_ms=elapsed,
        risk_level=risk,
        entities_found=entities,
        session_key=key,
    )
