import os, json
from fastapi import FastAPI, Request, Header, HTTPException
import httpx

AUTH = os.environ.get("AUTH_TOKEN") or "supersecret123"
PISTON_URL = "https://emkc.org/api/v2/piston/execute"

app = FastAPI()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/code/python")
async def run_python(req: Request, auth: str | None = Header(None)):
    # Auth
    if auth != AUTH:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Body
    try:
        body = await req.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

    code = body.get("code", "")
    if not isinstance(code, str) or not code:
        raise HTTPException(status_code=400, detail="Missing 'code'")

    piston_body = {
        "language": "python",
        "version": "3.10.0",
        "files": [{"name": "main.py", "content": code}],
        "stdin": "",
    }

    # Kall Piston trygt og returner ALDRI 500 til klienten pga parsing
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(PISTON_URL, json=piston_body)
            status = resp.status_code
            raw = await resp.aread()
            try:
                data = json.loads(raw.decode("utf-8", errors="ignore"))
            except Exception:
                data = {"raw": raw.decode("utf-8", errors="ignore")}
    except Exception as e:
        # Nettverksfeil / DNS / timeout etc.
        return {"error": "piston_request_failed", "details": str(e)}

    run = data.get("run", {}) if isinstance(data, dict) else {}

    # Returner både strukturert og rå info (lett å debugge i n8n)
    return {
        "status": status,
        "result": {
            "stdout": run.get("stdout", ""),
            "stderr": run.get("stderr", ""),
            "code": run.get("code", None),
            "output": run.get("output", None),
        },
        "piston_raw": data
    }
