import os, json
from fastapi import FastAPI, Request, Header, HTTPException
import httpx

AUTH = os.environ.get("AUTH_TOKEN") or "supersecret123"
PISTON_URL = "https://emkc.org/api/v2/piston/execute"

app = FastAPI()

@app.post("/code/python")
async def run_python(req: Request, auth: str | None = Header(None)):
    if auth != AUTH:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await req.json()
    code = body.get("code", "")
    if not isinstance(code, str) or not code:
        raise HTTPException(status_code=400, detail="Missing 'code'")

    piston_body = {
        "language": "python",
        "version": "3.10.0",
        "files": [{"name": "main.py", "content": code}],
        "stdin": "",
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(PISTON_URL, json=piston_body)
        r.raise_for_status()
        out = r.json()

    try:
        parsed = json.loads(out.get("run", {}).get("stdout", "") or "{}")
    except Exception:
        raise HTTPException(status_code=500, detail="stdout not JSON")

    return {"result": parsed}
