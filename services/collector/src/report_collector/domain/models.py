from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .enums import AdapterKind, DeliveryMode, RightsStatus, WorkflowStatus

TopicCode = Annotated[
    str,
    Field(
        pattern=r"^(economy|industry|ai-tech|labor-welfare|education-population|land-environment|law-security)$"
    ),
]


class SelectorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    list_item: str
    title: str
    detail_link: str
    published_at: str | None = None
    source_item_key_attr: str | None = None


class DetailConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    institution: str | None = None
    published_at: str | None = None
    attachments: str | None = None
    summary: str | None = None
    license: str | None = None


class FilterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed_extensions: list[str] = Field(default_factory=lambda: ["pdf", "hwp", "docx"])
    include_title_keywords: list[str] = Field(default_factory=list)
    exclude_title_keywords: list[str] = Field(default_factory=list)
    max_age_days: int = Field(default=1, ge=1, le=30)
    max_items_per_run: int = Field(default=20, ge=1, le=50)


class BrowserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wait_for: str | None = None
    timeout_ms: int = Field(default=30_000, ge=1_000, le=60_000)


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    adapter: AdapterKind
    homepage_url: HttpUrl
    list_url: HttpUrl
    rights_default: RightsStatus = RightsStatus.LINK_ONLY
    content_type: Literal["REPORT", "PRESS_RELEASE"] = "REPORT"
    poll_interval_minutes: int = Field(ge=60)
    request_delay_ms: int = Field(ge=500)
    timeout_seconds: float = Field(default=20, ge=1, le=60)
    run_timeout_seconds: int = Field(default=120, ge=30, le=600)
    max_retries: int = Field(default=2, ge=0, le=5)
    active: bool = True
    implementation: str | None = None
    detail_url_template: str | None = None
    source_item_key_pattern: str | None = None
    selectors: SelectorConfig | None = None
    detail: DetailConfig = Field(default_factory=DetailConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)


class DiscoveredItem(BaseModel):
    source_item_key: str
    title: str
    detail_url: HttpUrl
    published_at: date | None = None


class Attachment(BaseModel):
    url: HttpUrl
    file_name: str
    declared_type: str | None = None


class SourceDocument(BaseModel):
    source_item_key: str
    title: str
    institution: str
    detail_url: HttpUrl
    published_at: date | None = None
    attachments: list[Attachment] = Field(default_factory=list)
    official_summary: str | None = Field(default=None, max_length=3_000)
    license_text: str | None = None
    rights_status: RightsStatus = RightsStatus.LINK_ONLY


class SourceHealthResult(BaseModel):
    healthy: bool
    checked_at: datetime
    message: str


class AnalysisRequest(BaseModel):
    title: str
    institution: str
    text: str
    page_count: int | None = None


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    why_it_matters: str = Field(min_length=1, max_length=240)
    summary_kind: Literal["ANALYZED", "OFFICIAL_ABSTRACT", "UNAVAILABLE"] = "UNAVAILABLE"
    key_points: list[str] = Field(min_length=1, max_length=3)
    key_tags: list[str] = Field(min_length=1, max_length=3)
    topic_candidates: list[TopicCode] = Field(min_length=1)
    content_tag: str = Field(min_length=1, max_length=40)
    confidence: float = Field(ge=0, le=1)
    evidence_pages: list[int] = Field(default_factory=list)


class PublicationDocument(BaseModel):
    id: str
    title: str
    institution: str
    published_at: date
    primary_topic: TopicCode
    content_tag: str
    why_it_matters: str
    summary_kind: Literal["ANALYZED", "OFFICIAL_ABSTRACT", "UNAVAILABLE"] = "UNAVAILABLE"
    key_points: list[str] = Field(min_length=1, max_length=3)
    key_tags: list[str] = Field(min_length=1, max_length=3)
    delivery_mode: DeliveryMode
    source_url: HttpUrl
    download_url: HttpUrl | None = None
    format: str | None = None
    size_bytes: int | None = None
    page_count: int | None = None
    workflow_status: WorkflowStatus
    source_content_type: Literal["REPORT", "PRESS_RELEASE"] = "REPORT"
    ranking_score: float = 0
