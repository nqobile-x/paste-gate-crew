import os
import uvicorn


def main():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "paste_gate_crew.api:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
