from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import agent6
from demo_schemas import (
    ProjectMetaResponse,
    ProjectModuleInfo,
    ResetStateResponse,
    RunAllRequest,
    RunChatRequest,
    RunQueryRequest,
    RunResponse,
    StateSummaryResponse,
)
from memory import MemoryStore


app = FastAPI(title="Session6 Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


MODULES = [
    ProjectModuleInfo(
        name="Perception",
        path="perception.py",
        role="Classify user intent and extract typed query attributes.",
    ),
    ProjectModuleInfo(
        name="Memory",
        path="memory.py",
        role="Persist and retrieve durable memory under state/.",
    ),
    ProjectModuleInfo(
        name="Decision",
        path="decision.py",
        role="Choose final answer, memory write, or typed tool call.",
    ),
    ProjectModuleInfo(
        name="Action",
        path="action.py",
        role="Execute tools through MCP stdio and return typed results.",
    ),
    ProjectModuleInfo(
        name="Orchestrator",
        path="agent6.py",
        role="Run cognitive loop and evaluate convergence/pass criteria.",
    ),
    ProjectModuleInfo(
        name="Schemas",
        path="schemas.py",
        role="Pydantic v2 contracts for all boundaries and traces.",
    ),
    ProjectModuleInfo(
        name="MCP Server",
        path="mcp_server.py",
        role="Tool server over stdio transport.",
    ),
]


CONSTRAINTS = [
    "Pydantic v2 contracts on every boundary.",
    "LLM Gateway V3 is used for all LLM calls.",
    "MCP stdio transport is used for all tool execution.",
    "Durable memory persists under state/ across runs.",
    "No third-party agent framework is used.",
]


COMMANDS = [
    "uv sync",
    "cd llm_gatewayV3 && uv run python main.py",
    "uv run python demo_api.py",
    "cd frontend && npm install && npm run dev",
    "uv run python agent6.py --all --clean-state",
]


@app.get("/api/project-meta", response_model=ProjectMetaResponse)
async def project_meta() -> ProjectMetaResponse:
    return ProjectMetaResponse(
        title="Session6 Four-Layer Agent Demo",
        summary="Live demo surface for architecture, typed traces, memory persistence, and pass/fail validation.",
        modules=MODULES,
        constraints=CONSTRAINTS,
        commands=COMMANDS,
        target_queries=list(agent6.TARGETS.keys()),
    )


@app.post("/api/run/query", response_model=RunResponse)
async def run_query(payload: RunQueryRequest) -> RunResponse:
    query_id = payload.query_id.strip().upper()
    if query_id not in agent6.TARGETS:
        raise HTTPException(status_code=400, detail=f"Unknown query_id '{payload.query_id}'")
    results = await agent6.run_targets([query_id], clean_state=payload.clean_state)
    return RunResponse(
        results=results,
        overall_pass=all(item.passed for item in results),
        ran_at=datetime.now(timezone.utc),
    )


@app.post("/api/run/chat", response_model=RunResponse)
async def run_chat(payload: RunChatRequest) -> RunResponse:
    result = await agent6.run_adhoc_query(
        payload.query,
        max_iterations=payload.max_iterations,
        clean_state=payload.clean_state,
    )
    return RunResponse(
        results=[result],
        overall_pass=result.passed,
        ran_at=datetime.now(timezone.utc),
    )


@app.post("/api/run/all", response_model=RunResponse)
async def run_all(payload: RunAllRequest) -> RunResponse:
    results = await agent6.run_targets(agent6.ALL_QUERY_SEQUENCE, clean_state=payload.clean_state)
    return RunResponse(
        results=results,
        overall_pass=all(item.passed for item in results),
        ran_at=datetime.now(timezone.utc),
    )


@app.get("/api/state/summary", response_model=StateSummaryResponse)
async def state_summary() -> StateSummaryResponse:
    store = MemoryStore()
    state = store.load_state()
    return StateSummaryResponse(
        record_count=len(state.records),
        records=state.records,
        last_updated=state.last_updated,
    )


@app.post("/api/state/reset", response_model=ResetStateResponse)
async def state_reset() -> ResetStateResponse:
    store = MemoryStore()
    store.reset_state()
    return ResetStateResponse(ok=True, message="state/memory.json reset successfully")


if __name__ == "__main__":
    uvicorn.run("demo_api:app", host="0.0.0.0", port=8110, reload=True)
