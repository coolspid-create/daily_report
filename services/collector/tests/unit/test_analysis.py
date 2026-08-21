import json
from pathlib import Path

import pytest
from report_collector.domain.models import AnalysisRequest
from report_collector.providers.ai.mock_provider import MockAnalysisProvider
from report_collector.services.summarization_service import SummarizationService


@pytest.mark.asyncio
async def test_mock_analysis_matches_contract(contract_root: Path) -> None:
    schema = json.loads((contract_root / "analysis-result.schema.json").read_text(encoding="utf-8"))
    service = SummarizationService(MockAnalysisProvider(), schema)
    result = await service.summarize(
        AnalysisRequest(
            title="AI 산업 전략",
            institution="공공연구원",
            text="AI 도입은 산업 생산성을 높입니다. 책임 있는 활용 기준이 필요합니다.",
            page_count=2,
        )
    )
    assert result.topic_candidates[0] == "ai-tech"
    assert len(result.key_points) <= 3
    assert len(result.key_tags) <= 3
    assert all(page <= 2 for page in result.evidence_pages)
