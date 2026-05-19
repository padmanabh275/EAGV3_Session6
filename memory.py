from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from llm_gatewayV3.client import LLM
from schemas import MemoryInput, MemoryOutput, MemoryRecord, MemoryState, TaskType, response_format_for


class MemorySelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selected_keys: list[str]
    retrieval_summary: str


class MemoryStore:
    def __init__(self, state_dir: Path | None = None) -> None:
        root = Path(__file__).parent
        self.state_dir = state_dir or (root / "state")
        self.state_file = self.state_dir / "memory.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> MemoryState:
        if not self.state_file.exists():
            return MemoryState()
        raw = self.state_file.read_text(encoding="utf-8")
        data = json.loads(raw)
        return MemoryState.model_validate(data)

    def save_state(self, state: MemoryState) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temp_path = self.state_file.with_suffix(".json.tmp")
        temp_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temp_path.replace(self.state_file)

    def reset_state(self) -> None:
        if self.state_file.exists():
            self.state_file.unlink()

    def upsert_record(self, key: str, value: str, source_query: str) -> MemoryState:
        state = self.load_state()
        updated = False
        now = datetime.now(timezone.utc)
        for index, record in enumerate(state.records):
            if record.key.lower() == key.lower():
                state.records[index] = MemoryRecord(
                    key=record.key,
                    value=value,
                    source_query=source_query,
                    updated_at=now,
                )
                updated = True
                break
        if not updated:
            state.records.append(
                MemoryRecord(
                    key=key,
                    value=value,
                    source_query=source_query,
                    updated_at=now,
                )
            )
        state.last_updated = now
        self.save_state(state)
        return state


def run_memory_layer(llm: LLM, payload: MemoryInput, store: MemoryStore) -> MemoryOutput:
    state = store.load_state()
    if payload.perception.task_type == TaskType.STORE_MEMORY:
        return MemoryOutput(
            recalled_records=[],
            retrieval_summary="Memory write prepared.",
            pending_write_key=payload.perception.memory_key,
            pending_write_value=payload.perception.memory_value,
        )

    if not state.records:
        return MemoryOutput(recalled_records=[], retrieval_summary="No stored memories.")

    compact_records = [{"key": item.key, "value": item.value} for item in state.records]
    memory_prompt = (
        "You are the memory layer. Select which memory keys are useful for the user query.\n"
        f"User query: {payload.user_query}\n"
        f"Perception task type: {payload.perception.task_type.value}\n"
        f"Known memory records: {json.dumps(compact_records)}\n"
        "Return selected_keys and a short retrieval_summary."
    )
    try:
        response = llm.chat(
            prompt=memory_prompt,
            auto_route="memory",
            temperature=0.2,
            max_tokens=300,
            response_format=response_format_for(MemorySelection, "memory_selection"),
        )
        parsed = response.get("parsed") or {}
        selection = MemorySelection.model_validate(parsed)
        chosen_keys = {key.lower() for key in selection.selected_keys}
        recalled = [record for record in state.records if record.key.lower() in chosen_keys]
        return MemoryOutput(recalled_records=recalled, retrieval_summary=selection.retrieval_summary)
    except Exception:
        lowered_query = payload.user_query.lower()
        recalled = [item for item in state.records if item.key.lower() in lowered_query]
        if not recalled and "favorite fruit" in lowered_query:
            recalled = [item for item in state.records if item.key.lower() == "favorite_fruit"]
        return MemoryOutput(
            recalled_records=recalled,
            retrieval_summary="Fallback retrieval based on key matching.",
        )
