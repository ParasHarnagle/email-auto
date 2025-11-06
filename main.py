from runner import run_email_agent_prompt
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from pydantic import BaseModel

class Prompt(BaseModel):
    prompt: str
    user_id: str

app = FastAPI(
    title="Email Reading API",
    description="An API for reading and summarizing unread emails from a user's Gmail Primary tab.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ai/execute_email_runner")
async def execute_email_runner():
    t0 = time.time()
    try:
        prompt = "Summarize the unread emails on my Gmail "
        user_id = "test_user_123"
        result = await run_email_agent_prompt(prompt, user_id)
        duration_ms = round((time.time() - t0) * 1000, 2)
        return {
            "ok": True,
            "duration_ms": duration_ms,
            "prompt": prompt,
            "result": result
        }
    except Exception as e:
        duration_ms = round((time.time() - t0) * 1000, 2)
        # include schema snapshot to help the caller recover
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "duration_ms": duration_ms,
            },
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"} 
    
