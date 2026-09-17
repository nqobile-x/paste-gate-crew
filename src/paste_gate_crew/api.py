import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg  # type: ignore[assignment]

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from paste_gate_crew.crew import PasteGateCrew

VAULT_DIR = Path("obsidian_reports")
STATIC_DIR = Path(__file__).parent / "static"


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


@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.4.0"}


@app.post("/scrub", response_model=ScrubResponse)
async def scrub(req: ScrubRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty")

    t0 = time.monotonic()

    loop = asyncio.get_event_loop()

    def run_crew():
        for attempt in range(4):
            try:
                return PasteGateCrew().crew().kickoff(
                    inputs={"raw_text": req.text, "scrubbed_text": ""}
                )
            except Exception as e:
                msg = str(e).lower()
                if "rate_limit" in msg or "ratelimit" in msg or "rate limit" in msg:
                    wait = 2 ** attempt  # 1s, 2s, 4s, 8s
                    time.sleep(wait)
                    continue
                raise
        raise HTTPException(status_code=429, detail="Groq rate limit — please retry in a few seconds")

    result = await loop.run_in_executor(None, run_crew)

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
