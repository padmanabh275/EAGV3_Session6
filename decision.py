from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from llm_gatewayV3.client import LLM
from schemas import (
    CurrencyConvertArgs,
    CurrencyConvertInvocation,
    DecisionInput,
    DecisionOutput,
    DecisionType,
    FetchUrlArgs,
    FetchUrlInvocation,
    GetTimeArgs,
    GetTimeInvocation,
    ListDirArgs,
    ListDirInvocation,
    ReadFileArgs,
    ReadFileInvocation,
    ToolName,
    UpdateFileArgs,
    UpdateFileInvocation,
    WebSearchArgs,
    WebSearchInvocation,
    CreateFileArgs,
    CreateFileInvocation,
    EditFileArgs,
    EditFileInvocation,
    response_format_for,
)


class ToolChoiceEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: ToolName


DECISION_PROMPT_TEMPLATE = """You are the Decision layer.
Choose the next step using the provided typed context.

Rules:
- If enough information is available, return decision_type=final_answer.
- If a tool call is needed, return decision_type=call_tool and include a tool object.
- If a memory write is required, return decision_type=write_memory with memory_key and memory_value.
- Keep rationale short.

Context:
query_id: {query_id}
user_query: {user_query}
perception: {perception_json}
memory: {memory_json}
iteration: {iteration}/{max_iterations}
"""


TOOL_ARG_PROMPT_TEMPLATE = """Produce arguments for the tool in strict JSON.
tool_name: {tool_name}
user_query: {user_query}
"""


def _infer_tool_invocation(llm: LLM, tool_name: ToolName, user_query: str):
    prompt = TOOL_ARG_PROMPT_TEMPLATE.format(tool_name=tool_name.value, user_query=user_query)
    if tool_name == ToolName.WEB_SEARCH:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=200,
            response_format=response_format_for(WebSearchArgs, "web_search_args"),
        ).get("parsed") or {}
        return WebSearchInvocation(tool_name="web_search", arguments=WebSearchArgs.model_validate(parsed))
    if tool_name == ToolName.FETCH_URL:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=200,
            response_format=response_format_for(FetchUrlArgs, "fetch_url_args"),
        ).get("parsed") or {}
        return FetchUrlInvocation(tool_name="fetch_url", arguments=FetchUrlArgs.model_validate(parsed))
    if tool_name == ToolName.GET_TIME:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=200,
            response_format=response_format_for(GetTimeArgs, "get_time_args"),
        ).get("parsed") or {}
        return GetTimeInvocation(tool_name="get_time", arguments=GetTimeArgs.model_validate(parsed))
    if tool_name == ToolName.CURRENCY_CONVERT:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=200,
            response_format=response_format_for(CurrencyConvertArgs, "currency_convert_args"),
        ).get("parsed") or {}
        return CurrencyConvertInvocation(
            tool_name="currency_convert",
            arguments=CurrencyConvertArgs.model_validate(parsed),
        )
    if tool_name == ToolName.READ_FILE:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=200,
            response_format=response_format_for(ReadFileArgs, "read_file_args"),
        ).get("parsed") or {}
        return ReadFileInvocation(tool_name="read_file", arguments=ReadFileArgs.model_validate(parsed))
    if tool_name == ToolName.LIST_DIR:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=200,
            response_format=response_format_for(ListDirArgs, "list_dir_args"),
        ).get("parsed") or {}
        return ListDirInvocation(tool_name="list_dir", arguments=ListDirArgs.model_validate(parsed))
    if tool_name == ToolName.CREATE_FILE:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=250,
            response_format=response_format_for(CreateFileArgs, "create_file_args"),
        ).get("parsed") or {}
        return CreateFileInvocation(tool_name="create_file", arguments=CreateFileArgs.model_validate(parsed))
    if tool_name == ToolName.UPDATE_FILE:
        parsed = llm.chat(
            prompt=prompt,
            auto_route="decision",
            temperature=0.2,
            max_tokens=250,
            response_format=response_format_for(UpdateFileArgs, "update_file_args"),
        ).get("parsed") or {}
        return UpdateFileInvocation(tool_name="update_file", arguments=UpdateFileArgs.model_validate(parsed))
    parsed = llm.chat(
        prompt=prompt,
        auto_route="decision",
        temperature=0.2,
        max_tokens=250,
        response_format=response_format_for(EditFileArgs, "edit_file_args"),
    ).get("parsed") or {}
    return EditFileInvocation(tool_name="edit_file", arguments=EditFileArgs.model_validate(parsed))


def _default_tool_invocation(tool_name: ToolName, user_query: str):
    if tool_name == ToolName.GET_TIME:
        return GetTimeInvocation(tool_name="get_time", arguments=GetTimeArgs(timezone="UTC"))
    if tool_name == ToolName.CURRENCY_CONVERT:
        return CurrencyConvertInvocation(
            tool_name="currency_convert",
            arguments=CurrencyConvertArgs(amount=10, from_currency="USD", to_currency="INR"),
        )
    if tool_name == ToolName.WEB_SEARCH:
        return WebSearchInvocation(tool_name="web_search", arguments=WebSearchArgs(query=user_query, max_results=3))
    if tool_name == ToolName.LIST_DIR:
        return ListDirInvocation(tool_name="list_dir", arguments=ListDirArgs(path="."))
    if tool_name == ToolName.READ_FILE:
        return ReadFileInvocation(tool_name="read_file", arguments=ReadFileArgs(path="notes.txt"))
    if tool_name == ToolName.FETCH_URL:
        return FetchUrlInvocation(tool_name="fetch_url", arguments=FetchUrlArgs(url="https://example.com"))
    if tool_name == ToolName.CREATE_FILE:
        return CreateFileInvocation(
            tool_name="create_file",
            arguments=CreateFileArgs(path="note.txt", content="hello"),
        )
    if tool_name == ToolName.UPDATE_FILE:
        return UpdateFileInvocation(
            tool_name="update_file",
            arguments=UpdateFileArgs(path="note.txt", content="updated"),
        )
    return EditFileInvocation(
        tool_name="edit_file",
        arguments=EditFileArgs(path="note.txt", find="old", replace="new"),
    )


def run_decision_layer(llm: LLM, payload: DecisionInput) -> DecisionOutput:
    try:
        response = llm.chat(
            prompt=DECISION_PROMPT_TEMPLATE.format(
                query_id=payload.query_id,
                user_query=payload.user_query,
                perception_json=payload.perception.model_dump_json(),
                memory_json=payload.memory.model_dump_json(),
                iteration=payload.iteration,
                max_iterations=payload.max_iterations,
            ),
            auto_route="decision",
            temperature=0.2,
            max_tokens=500,
            response_format=response_format_for(DecisionOutput, "decision_output"),
        )
        parsed = response.get("parsed") or {}
        decision = DecisionOutput.model_validate(parsed)
    except Exception:
        if payload.perception.requires_tool and payload.perception.suggested_tool is not None:
            return DecisionOutput(
                decision_type=DecisionType.CALL_TOOL,
                rationale="Fallback decision due gateway failure.",
                tool=_default_tool_invocation(payload.perception.suggested_tool, payload.user_query),
            )
        if payload.perception.memory_key and payload.perception.memory_value:
            return DecisionOutput(
                decision_type=DecisionType.WRITE_MEMORY,
                rationale="Fallback memory write due gateway failure.",
                memory_key=payload.perception.memory_key,
                memory_value=payload.perception.memory_value,
            )
        if payload.memory.recalled_records:
            first = payload.memory.recalled_records[0]
            return DecisionOutput(
                decision_type=DecisionType.FINAL_ANSWER,
                rationale="Fallback memory answer due gateway failure.",
                final_answer=f"{first.key}: {first.value}",
            )
        return DecisionOutput(
            decision_type=DecisionType.FINAL_ANSWER,
            rationale="Fallback direct answer due gateway failure.",
            final_answer="Unable to decide a tool step reliably.",
        )

    if decision.decision_type == DecisionType.CALL_TOOL and decision.tool is None:
        tool_name = payload.perception.suggested_tool
        if tool_name is None:
            tool_choice = llm.chat(
                prompt=(
                    "Choose the best tool name for this query from the allowed enum.\n"
                    f"query: {payload.user_query}"
                ),
                auto_route="decision",
                temperature=0.1,
                max_tokens=100,
                response_format=response_format_for(ToolChoiceEnvelope, "tool_choice"),
            ).get("parsed") or {}
            tool_name = ToolChoiceEnvelope.model_validate(tool_choice).tool_name
        try:
            decision.tool = _infer_tool_invocation(llm, tool_name, payload.user_query)
        except Exception:
            decision.tool = _default_tool_invocation(tool_name, payload.user_query)

    if (
        decision.decision_type == DecisionType.FINAL_ANSWER
        and not decision.final_answer
        and payload.memory.recalled_records
    ):
        first = payload.memory.recalled_records[0]
        decision.final_answer = f"{first.key}: {first.value}"
    return decision
