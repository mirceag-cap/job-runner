from fastapi import FastAPI, Request
import json
from datetime import datetime, timezone

app = FastAPI()

@app.post('/alerts')
async def alerts(req: Request):
    payload = await req.json()
    print("/n" + '=' * 80)
    print(datetime.now(timezone.utc).isoformat(), "UTC ALERTS RECEIVED")
    print(json.dumps(payload, indent=2))
    print("=" * 80)
    return {"ok": True}