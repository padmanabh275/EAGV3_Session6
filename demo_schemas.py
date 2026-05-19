from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas import MemoryRecord, RunResult


class ProjectModuleInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    path: str
    role: str


class ProjectMetaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    summary: str
    modules: list[ProjectModuleInfo]
    constraints: list[str]
    commands: list[str]
    target_queries: list[str]


class RunQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    clean_state: bool = False


class RunAllRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clean_state: bool = True


class RunChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1)
    max_iterations: int = Field(default=4, ge=1, le=16)
    clean_state: bool = False


class RunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: list[RunResult]
    overall_pass: bool
    ran_at: datetime


class StateSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_count: int
    records: list[MemoryRecord] = Field(default_factory=list)
    last_updated: datetime | None = None


class ResetStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    message: str
