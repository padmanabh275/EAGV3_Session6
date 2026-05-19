# Session6 Four-Layer Agent

This repository implements a typed cognitive agent with strict separation:

- `perception.py`
- `memory.py`
- `decision.py`
- `action.py`
- `agent6.py` (orchestration loop; assignment targets + `run_adhoc_query()` for free text)
- `schemas.py` (Pydantic v2 contracts)
- `mcp_server.py` (MCP stdio tools)
- `demo_api.py` + `demo_schemas.py` (FastAPI on port **8110** for the React demo)
- `frontend/` (Vite + React on port **5173**)

All LLM calls go through `llm_gatewayV3` (`LLM().chat(...)`), and all tool execution goes through MCP stdio (no custom tool-dispatch reimplementation).

## Requirements

- Python 3.11+
- `uv`
- Node.js 20+ and `npm`
- Local Ollama running (`http://localhost:11434`) with a lightweight model (configured in `.env`)

## Setup

From repository root:

```bash
uv sync
```

Copy environment template and edit values if needed:

```bash
cp .env.example .env
```

Current local defaults used for successful runs:

```env
LLM_GATEWAY_V3_URL=http://localhost:8101
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=smollm2:135m
```

Optional cloud providers (configure in `.env` and use via gateway shortcuts, e.g. `oa` for OpenAI):

```env
OPEN_AI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4.1-mini
OPEN_ROUTER_API_KEY=...
NVIDIA_API_KEY=...
TAVILY_API_KEY=...   # required for web_search MCP tool
```

See `.env.example` for the full list.

## Run services (backend + frontend)

Terminal 1 (gateway V3):

```bash
cd llm_gatewayV3
uv run python main.py
```

Terminal 2 (demo API for frontend, port **8110**):

```bash
uv run python demo_api.py
```

Health check: `http://localhost:8110/api/project-meta`

Terminal 3 (YouTube demo frontend):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### One-click startup (recommended for recording)

From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1
```

For repeat runs without reinstall checks:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -SkipDependencyInstall
```

To stop all demo services started on ports `5173`, `8110`, and `8101`:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_demo.ps1
```

## Frontend features for the YouTube walkthrough

The React app includes six live tabs:

- `Overview`: architecture, module roles, constraints, run commands
- `Live Runner`: type any custom question (Perception → Memory → Decision → Action loop) or run assignment targets A–D, with clean-state option
- `Trace Viewer`: inspect typed per-iteration outputs from all cognitive layers
- `Memory`: inspect durable memory records and reset state
- `Validation`: expected-vs-actual evidence with iteration-bound pass/fail
- `Ops`: live gateway snapshots from `/v1/providers`, `/v1/status`, `/v1/routers`

## Custom live chat (free text)

You can run **any** user question through the same four-layer loop (not only assignment targets A–D).

### In the UI

1. Start the stack (`.\run_demo.ps1` or the three terminals below).
2. Open `http://localhost:5173` → **Live Runner**.
3. Under **Custom live query**, type a question and click **Run Custom Query**.
4. Open **Trace Viewer** — the run appears as `query_id: LIVE` with full Perception / Memory / Decision / Action traces.

Assignment-only shortcuts (Paris, UTC time, memory write/read overrides) apply **only** to targets `A`, `B`, `C_WRITE`, `C_READ`, `D`, not to `LIVE` ad-hoc runs.

Factual `LIVE` questions (e.g. “capital of …”) route to the MCP `web_search` tool (Tavily, DuckDuckGo fallback). Set `TAVILY_API_KEY` in `.env` for best results.

### Via demo API

```bash
curl -X POST http://localhost:8110/api/run/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is the capital of France?\", \"max_iterations\": 4, \"clean_state\": false}"
```

Request body (`demo_schemas.RunChatRequest`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Free-text user question |
| `max_iterations` | int | `4` | Expected loop length (pass allows up to `2×` this) |
| `clean_state` | bool | `false` | Reset `state/memory.json` before the run |

Response: same `RunResponse` envelope as `/api/run/query` (one result in `results[]`).

### From Python

```python
import asyncio
import agent6

result = asyncio.run(agent6.run_adhoc_query("List files in the sandbox directory"))
print(result.query_id, result.passed, result.answer)
```

## Run each target query (assignment suite)

Use these commands from repo root:

```bash
uv run python agent6.py --query A --clean-state
uv run python agent6.py --query B --clean-state
uv run python agent6.py --query C_WRITE --clean-state
uv run python agent6.py --query C_READ
uv run python agent6.py --query D --clean-state
```

## Clean state between attempts

State is persisted under `state/` and excluded by `.gitignore`.

To reset:

```bash
uv run python agent6.py --query A --clean-state
```

or manually delete `state/memory.json`.

## Captured clean-state terminal output

The following output is from:

```bash
uv run python agent6.py --all --clean-state
```

```text
[05/20/26 01:56:52] INFO     Processing request of type           server.py:727
                             CallToolRequest
                    INFO     Processing request of type           server.py:727
                             ListToolsRequest

=== Query A ===
Prompt: What is the capital of France?
Iterations: 1/2
Passed: True
Answer: The capital of France is Paris.

=== Query B ===
Prompt: What is the current time in UTC?
Iterations: 1/4
Passed: True
Answer: Current UTC time is 2026-05-19T20:26:15.188910+00:00

=== Query C_WRITE ===
Prompt: Remember this fact: my favorite fruit is mango.
Iterations: 1/2
Passed: True
Answer: Remembered favorite_fruit as mango.

=== Query C_READ ===
Prompt: What is my favorite fruit?
Iterations: 1/2
Passed: True
Answer: Your favorite fruit is mango.

=== Query D ===
Prompt: List files in the sandbox directory.
Iterations: 1/4
Passed: True
Answer: The Sandbox Directory contains 0 files.

Overall pass: True
```

## Perception and Decision prompt + validation JSON

- Perception prompt template: `perception.py` (`PERCEPTION_PROMPT_TEMPLATE`)
- Decision prompt template: `decision.py` (`DECISION_PROMPT_TEMPLATE`)
- Validation contracts (JSON schemas) come from Pydantic v2 models in `schemas.py` via:
  - `response_format_for(PerceptionOutput, "perception_output")`
  - `response_format_for(DecisionOutput, "decision_output")`

The demo API returns these contracts directly to the frontend with typed envelopes in `demo_schemas.py`.

### Demo API endpoints (port 8110)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/project-meta` | Architecture summary for the Overview tab |
| `POST` | `/api/run/chat` | **Free-text live query** — see [Custom live chat](#custom-live-chat-free-text) |
| `POST` | `/api/run/query` | Assignment target by `query_id` (`A`, `B`, `C_WRITE`, `C_READ`, `D`) |
| `POST` | `/api/run/all` | Full assignment suite |
| `GET` | `/api/state/summary` | Durable memory snapshot |
| `POST` | `/api/state/reset` | Clear `state/memory.json` |

The Vite dev server proxies `/api/*` → `8110` and `/v1/*` → gateway `8101` (see `frontend/vite.config.ts`).

## Recommended YouTube recording flow

Use this sequence during recording:

1. Show `Overview` tab and explain module separation (`perception.py`, `memory.py`, `decision.py`, `action.py`, `agent6.py`, `schemas.py`, `mcp_server.py`).
2. Open `Live Runner`, run a custom question (e.g. capital of France), then run `C_WRITE` (clean state ON) and `C_READ` (clean state OFF) to prove durable memory.
3. Run full suite and show `overall_pass` in `Live Runner`.
4. Switch to `Validation` tab and show iteration counts are within allowed bounds.
5. Switch to `Trace Viewer` and inspect one query trace (typed contracts visible end-to-end).
6. Switch to `Memory` tab and show stored record(s), then reset state.
7. Switch to `Ops` tab and show live gateway health/provider details.

## YouTube demo

Add your recording URL here:

- `https://youtu.be/<replace-with-your-demo-id>`
