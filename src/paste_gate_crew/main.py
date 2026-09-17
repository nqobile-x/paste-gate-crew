import sys
import os
from datetime import datetime
from pathlib import Path

# Groq rejects messages that carry the cache_breakpoint key crewai injects.
# Patch the marker to a no-op so the key is never added.
import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg  # type: ignore[assignment]

from paste_gate_crew.crew import PasteGateCrew

VAULT_DIR = Path(r"C:\Users\Geeks2_PC18\Documents\Obsidian Vault\Paste Gate")

SAMPLE_INPUT = (
    "Hi, my name is Nqobile Dlamini. My SA ID is 9001015009087. "
    "You can reach me at nqobile@fnb.co.za or call +27 82 345 6789. "
    "My API key is sk-abc123XYZ and the internal host is db.internal.fnb.co.za."
)


def save_to_vault(raw_text: str, result: str) -> Path:
    """Write the crew output to the Obsidian vault and return the file path."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = VAULT_DIR / "reports" / f"redaction-{timestamp}.md"

    frontmatter = (
        "---\n"
        f"date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"tags: [paste-gate, redaction]\n"
        "---\n\n"
    )
    input_section = f"## Input\n\n```\n{raw_text}\n```\n\n---\n\n"

    report_path.write_text(frontmatter + input_section + result, encoding="utf-8")
    return report_path


def run():
    """Run the Paste Gate crew with raw text input."""
    if len(sys.argv) > 1:
        raw_text = " ".join(sys.argv[1:])
    else:
        raw_text = SAMPLE_INPUT
        print(f"No input provided — using sample text:\n{raw_text}\n")

    inputs = {"raw_text": raw_text, "scrubbed_text": ""}
    result = PasteGateCrew().crew().kickoff(inputs=inputs)

    report_path = save_to_vault(raw_text, str(result))
    print(f"\n✓ Report saved to Obsidian vault:\n  {report_path}")


def train():
    """Train the crew for a given number of iterations."""
    inputs = {"raw_text": "Sample text with John Smith, ID 8001015009087, john@example.com"}
    try:
        PasteGateCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}") from e


if __name__ == "__main__":
    run()
