# Session6 Four-Layer Agent

This repository implements a typed cognitive agent with strict separation:

- `perception.py`
- `memory.py`
- `decision.py`
- `action.py`
- `agent6.py` (orchestration loop)
- `schemas.py` (Pydantic v2 contracts)
- `mcp_server.py` (MCP stdio tools)

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

## Run services (backend + frontend)

Terminal 1 (gateway V3):

```bash
cd llm_gatewayV3
uv run python main.py
```

Terminal 2 (demo API for frontend):

```bash
uv run python demo_api.py
```

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
- `Live Runner`: run one query or full suite, with clean-state option
- `Trace Viewer`: inspect typed per-iteration outputs from all cognitive layers
- `Memory`: inspect durable memory records and reset state
- `Validation`: expected-vs-actual evidence with iteration-bound pass/fail
- `Ops`: live gateway snapshots from `/v1/providers`, `/v1/status`, `/v1/routers`

## Run each target query

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

## Recommended YouTube recording flow

Use this sequence during recording:

1. Show `Overview` tab and explain module separation (`perception.py`, `memory.py`, `decision.py`, `action.py`, `agent6.py`, `schemas.py`, `mcp_server.py`).
2. Open `Live Runner` and run `C_WRITE` (clean state ON), then `C_READ` (clean state OFF) to prove durable memory.
3. Run full suite and show `overall_pass` in `Live Runner`.
4. Switch to `Validation` tab and show iteration counts are within allowed bounds.
5. Switch to `Trace Viewer` and inspect one query trace (typed contracts visible end-to-end).
6. Switch to `Memory` tab and show stored record(s), then reset state.
7. Switch to `Ops` tab and show live gateway health/provider details.

## YouTube demo

Add your recording URL here:

- `https://youtu.be/<replace-with-your-demo-id>`
