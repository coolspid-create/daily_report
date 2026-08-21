import json
from pathlib import Path

import pytest
from report_collector.domain.models import AnalysisRequest
from report_collector.providers.ai.extractive_provider import ExtractiveAnalysisProvider
from report_collector.services.summarization_service import SummarizationService


@pytest.mark.asyncio
async def test_pdf_text_generates_source_derived_summary(contract_root: Path) -> None:
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text(encoding="utf-8"))
    result = await SummarizationService(ExtractiveAnalysisProvider(), schema).summarize(
        AnalysisRequest(
            title="자살예방 입법 과제",
            institution="국회입법조사처",
            text=(
                "자살은 개인의 심리적 문제를 넘어 사회경제적 요인이 복합적으로 작용하는 사회적 재난이다. "
                "본 보고서는 현행 자살예방법이 사회구조적 위험요인에 대응하는 법적 기반이 부족하다고 분석한다. "
                "자살유발환경 관리체계를 보완하고 사회복지체계와 연계하는 입법정책 과제를 제안한다."
            ),
            page_count=3,
        )
    )
    assert result.summary_kind == "ANALYZED"
    assert 2 <= len(result.key_points) <= 3
    assert "입법정책 과제" in result.why_it_matters
    assert len(result.key_tags) == 3


@pytest.mark.asyncio
async def test_short_pdf_text_is_not_presented_as_summary(contract_root: Path) -> None:
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text(encoding="utf-8"))
    result = await SummarizationService(ExtractiveAnalysisProvider(), schema).summarize(
        AnalysisRequest(title="짧은 자료", institution="기관", text="표지", page_count=1)
    )
    assert result.summary_kind == "UNAVAILABLE"


@pytest.mark.asyncio
async def test_sentence_fragment_is_not_presented_as_summary(contract_root: Path) -> None:
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text(encoding="utf-8"))
    result = await SummarizationService(ExtractiveAnalysisProvider(), schema).summarize(
        AnalysisRequest(
            title="깨진 PDF",
            institution="기관",
            text="이 문장은 PDF 열 순서가 깨져 중간에서 멈춘 문장 조각입니다 결과를 확인할 수",
            page_count=1,
        )
    )
    assert result.summary_kind == "UNAVAILABLE"


@pytest.mark.asyncio
async def test_provider_prefers_abstract_over_cover_and_contents(contract_root: Path) -> None:
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text(encoding="utf-8"))
    result = await SummarizationService(ExtractiveAnalysisProvider(), schema).summarize(
        AnalysisRequest(
            title="공공 AI 책임성 연구",
            institution="기관",
            text=(
                "공공 AI 책임성 연구 표지 발간사 목차 제1장 서론. "
                "국문초록 본 연구는 공공기관의 AI 도입 과정에서 책임성과 설명 가능성을 "
                "확보하기 위한 제도 기준과 기관별 관리 책임을 종합적으로 분석한다. "
                "고위험 업무에는 사전 영향평가와 이의제기 절차를 마련해 시민의 권리를 "
                "보호할 수 있도록 제도적 기준을 정비할 필요가 있다. 기관별 AI 책임자를 "
                "지정하고 독립적인 검증 체계를 운영하는 방안을 구체적으로 제안한다. 제1장 서론"
            ),
            page_count=3,
        )
    )
    assert result.summary_kind == "ANALYZED"
    assert "책임성과 설명 가능성" in result.why_it_matters
    assert "표지" not in result.why_it_matters
