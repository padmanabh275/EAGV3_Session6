from __future__ import annotations

import json
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from schemas import (
    ActionInput,
    ActionOutput,
    CurrencyConvertResult,
    EditFileResult,
    FetchUrlResult,
    FileWriteResult,
    GetTimeResult,
    ListDirResult,
    ReadFileResult,
    SearchItem,
    ToolName,
    WebSearchResult,
)


class MCPActionRunner:
    def __init__(self, server_script: str = "mcp_server.py") -> None:
        workspace = Path(__file__).parent
        self._server_script = str(workspace / server_script)
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "MCPActionRunner":
        params = StdioServerParameters(command="uv", args=["run", "python", self._server_script])
        transport = await self._stack.enter_async_context(stdio_client(params))
        read_stream, write_stream = transport
        self._session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._stack.aclose()

    async def execute(self, payload: ActionInput) -> ActionOutput:
        if self._session is None:
            raise RuntimeError("MCPActionRunner must be used within an async context manager.")
        tool_name = payload.invocation.tool_name
        args = payload.invocation.arguments.model_dump(by_alias=True)
        call_result = await self._session.call_tool(tool_name, args)
        normalized = self._normalize_tool_result(call_result)
        return self._typed_action_output(tool_name=ToolName(tool_name), data=normalized)

    @staticmethod
    def _normalize_tool_result(result: Any) -> Any:
        if hasattr(result, "structuredContent") and getattr(result, "structuredContent") is not None:
            return getattr(result, "structuredContent")
        if hasattr(result, "content"):
            content = getattr(result, "content")
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict) and "text" in first:
                    text = first["text"]
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
                if hasattr(first, "text"):
                    text = getattr(first, "text")
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
            return content
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result

    @staticmethod
    def _typed_action_output(tool_name: ToolName, data: Any) -> ActionOutput:
        if isinstance(data, str):
            return ActionOutput(tool_name=tool_name, summary=data)
        if tool_name == ToolName.WEB_SEARCH:
            if not isinstance(data, list):
                return ActionOutput(tool_name=tool_name, summary="web_search returned unexpected format.")
            rows = [SearchItem.model_validate(item) for item in data]
            return ActionOutput(
                tool_name=tool_name,
                summary=f"Retrieved {len(rows)} search results.",
                web_search=WebSearchResult(items=rows),
            )
        if tool_name == ToolName.FETCH_URL:
            parsed = FetchUrlResult.model_validate(data)
            return ActionOutput(tool_name=tool_name, summary="Fetched URL content.", fetch_url=parsed)
        if tool_name == ToolName.GET_TIME:
            parsed = GetTimeResult.model_validate(data)
            return ActionOutput(
                tool_name=tool_name,
                summary=f"Time fetched for {parsed.timezone}.",
                get_time=parsed,
            )
        if tool_name == ToolName.CURRENCY_CONVERT:
            parsed = CurrencyConvertResult.model_validate(data)
            return ActionOutput(
                tool_name=tool_name,
                summary=f"Converted {parsed.amount} {parsed.from_currency} to {parsed.to_currency}.",
                currency_convert=parsed,
            )
        if tool_name == ToolName.READ_FILE:
            parsed = ReadFileResult.model_validate(data)
            return ActionOutput(tool_name=tool_name, summary=f"Read file {parsed.path}.", read_file=parsed)
        if tool_name == ToolName.LIST_DIR:
            entries = data.get("result") if isinstance(data, dict) else data
            parsed = ListDirResult(entries=entries)
            return ActionOutput(
                tool_name=tool_name,
                summary=f"Listed {len(parsed.entries)} directory entries.",
                list_dir=parsed,
            )
        if tool_name == ToolName.CREATE_FILE:
            parsed = FileWriteResult.model_validate(data)
            return ActionOutput(tool_name=tool_name, summary=f"Created file {parsed.path}.", create_file=parsed)
        if tool_name == ToolName.UPDATE_FILE:
            parsed = FileWriteResult.model_validate(data)
            return ActionOutput(tool_name=tool_name, summary=f"Updated file {parsed.path}.", update_file=parsed)
        parsed = EditFileResult.model_validate(data)
        return ActionOutput(tool_name=tool_name, summary=f"Edited file {parsed.path}.", edit_file=parsed)
