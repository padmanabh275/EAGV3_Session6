from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class CognitiveRole(str, Enum):
    PERCEPTION = "perception"
    MEMORY = "memory"
    DECISION = "decision"
    ACTION = "action"


class ToolName(str, Enum):
    WEB_SEARCH = "web_search"
    FETCH_URL = "fetch_url"
    GET_TIME = "get_time"
    CURRENCY_CONVERT = "currency_convert"
    READ_FILE = "read_file"
    LIST_DIR = "list_dir"
    CREATE_FILE = "create_file"
    UPDATE_FILE = "update_file"
    EDIT_FILE = "edit_file"


class TaskType(str, Enum):
    DIRECT_ANSWER = "direct_answer"
    TOOL_REQUIRED = "tool_required"
    STORE_MEMORY = "store_memory"
    RECALL_MEMORY = "recall_memory"


class DecisionType(str, Enum):
    FINAL_ANSWER = "final_answer"
    CALL_TOOL = "call_tool"
    WRITE_MEMORY = "write_memory"


class SearchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    url: str
    snippet: str


class DirEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: Literal["dir", "file"]
    size_bytes: int


class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    value: str
    source_query: str
    updated_at: datetime


class MemoryState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[MemoryRecord] = Field(default_factory=list)
    last_updated: datetime | None = None


class PerceptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    user_query: str
    iteration: int = Field(ge=1)


class PerceptionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_type: TaskType
    normalized_query: str
    memory_key: str | None = None
    memory_value: str | None = None
    requires_tool: bool
    suggested_tool: ToolName | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class MemoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    user_query: str
    perception: PerceptionOutput
    state: MemoryState


class MemoryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recalled_records: list[MemoryRecord] = Field(default_factory=list)
    retrieval_summary: str = ""
    pending_write_key: str | None = None
    pending_write_value: str | None = None


class WebSearchArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    max_results: int = Field(default=3, ge=1, le=5)


class FetchUrlArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    timeout: int = Field(default=20, ge=1, le=120)


class GetTimeArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timezone: str = "UTC"


class CurrencyConvertArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: float
    from_currency: str
    to_currency: str


class ReadFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str


class ListDirArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = "."


class CreateFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content: str


class UpdateFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content: str


class EditFileArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    find: str
    replace: str
    replace_all: bool = False


class WebSearchInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["web_search"]
    arguments: WebSearchArgs


class FetchUrlInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["fetch_url"]
    arguments: FetchUrlArgs


class GetTimeInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["get_time"]
    arguments: GetTimeArgs


class CurrencyConvertInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["currency_convert"]
    arguments: CurrencyConvertArgs


class ReadFileInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["read_file"]
    arguments: ReadFileArgs


class ListDirInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["list_dir"]
    arguments: ListDirArgs


class CreateFileInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["create_file"]
    arguments: CreateFileArgs


class UpdateFileInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["update_file"]
    arguments: UpdateFileArgs


class EditFileInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["edit_file"]
    arguments: EditFileArgs


ToolInvocation = Annotated[
    (
        WebSearchInvocation
        | FetchUrlInvocation
        | GetTimeInvocation
        | CurrencyConvertInvocation
        | ReadFileInvocation
        | ListDirInvocation
        | CreateFileInvocation
        | UpdateFileInvocation
        | EditFileInvocation
    ),
    Field(discriminator="tool_name"),
]


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    user_query: str
    perception: PerceptionOutput
    memory: MemoryOutput
    iteration: int = Field(ge=1)
    max_iterations: int = Field(ge=1)


class DecisionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_type: DecisionType
    rationale: str
    final_answer: str | None = None
    tool: ToolInvocation | None = None
    memory_key: str | None = None
    memory_value: str | None = None


class WebSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[SearchItem]


class FetchUrlResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: int
    content_type: str
    length_bytes: int
    text: str


class GetTimeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    iso: str
    human: str
    timezone: str
    offset_hours: float


class CurrencyConvertResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: float
    from_currency: str
    to_currency: str = Field(alias="to")
    rate: float
    converted: float
    date: str
    source: str


class ReadFileResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    size_bytes: int
    content: str
    encoding: str


class ListDirResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entries: list[DirEntry]


class FileWriteResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    path: str
    size_bytes: int


class EditFileResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    path: str
    replacements: int
    size_bytes: int


class ActionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invocation: ToolInvocation


class ActionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: ToolName
    summary: str
    web_search: WebSearchResult | None = None
    fetch_url: FetchUrlResult | None = None
    get_time: GetTimeResult | None = None
    currency_convert: CurrencyConvertResult | None = None
    read_file: ReadFileResult | None = None
    list_dir: ListDirResult | None = None
    create_file: FileWriteResult | None = None
    update_file: FileWriteResult | None = None
    edit_file: EditFileResult | None = None


class IterationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    iteration: int
    perception: PerceptionOutput
    memory: MemoryOutput
    decision: DecisionOutput
    action: ActionOutput | None = None
    answer: str | None = None


class RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    user_query: str
    iterations: int
    answer: str
    passed: bool
    max_allowed_iterations: int
    traces: list[IterationTrace]


def response_format_for(model_cls: type[BaseModel], name: str) -> dict:
    return {
        "type": "json_schema",
        "schema": model_cls.model_json_schema(),
        "name": name,
        "strict": True,
    }
