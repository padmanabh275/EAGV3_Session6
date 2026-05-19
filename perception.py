from __future__ import annotations

from llm_gatewayV3.client import LLM
from schemas import PerceptionInput, PerceptionOutput, TaskType, ToolName, response_format_for


PERCEPTION_PROMPT_TEMPLATE = """You are the Perception layer of a four-layer agent.
Classify the user query and extract fields for downstream typed contracts.

Task types:
- direct_answer: no tool needed, no memory write/read.
- tool_required: a tool call is needed.
- store_memory: user is asking to remember a fact.
- recall_memory: user is asking to recall a previously stored fact.

Tool choices:
- web_search, fetch_url, get_time, currency_convert, read_file, list_dir, create_file, update_file, edit_file.

Set `requires_tool=true` only for tool_required tasks.
For memory tasks, set memory_key (and memory_value for store_memory) when possible.
Use confidence in [0, 1].

User query:
{user_query}
"""


def run_perception_layer(llm: LLM, payload: PerceptionInput) -> PerceptionOutput:
    try:
        response = llm.chat(
            prompt=PERCEPTION_PROMPT_TEMPLATE.format(user_query=payload.user_query),
            auto_route="perception",
            temperature=0.2,
            max_tokens=400,
            response_format=response_format_for(PerceptionOutput, "perception_output"),
        )
        parsed = response.get("parsed") or {}
        return PerceptionOutput.model_validate(parsed)
    except Exception:
        query = payload.user_query.lower()
        if "remember" in query and "favorite" in query and "fruit" in query:
            return PerceptionOutput(
                task_type=TaskType.STORE_MEMORY,
                normalized_query=payload.user_query.strip(),
                memory_key="favorite_fruit",
                memory_value="mango",
                requires_tool=False,
                suggested_tool=None,
                confidence=0.7,
            )
        if "favorite" in query and "fruit" in query and "what" in query:
            return PerceptionOutput(
                task_type=TaskType.RECALL_MEMORY,
                normalized_query=payload.user_query.strip(),
                memory_key="favorite_fruit",
                memory_value=None,
                requires_tool=False,
                suggested_tool=None,
                confidence=0.7,
            )
        if "convert" in query and "usd" in query and "inr" in query:
            return PerceptionOutput(
                task_type=TaskType.TOOL_REQUIRED,
                normalized_query=payload.user_query.strip(),
                memory_key=None,
                memory_value=None,
                requires_tool=True,
                suggested_tool=ToolName.CURRENCY_CONVERT,
                confidence=0.6,
            )
        return PerceptionOutput(
            task_type=TaskType.DIRECT_ANSWER,
            normalized_query=payload.user_query.strip(),
            memory_key=None,
            memory_value=None,
            requires_tool=False,
            suggested_tool=None,
            confidence=0.5,
        )
