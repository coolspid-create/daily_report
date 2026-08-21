from typing import Protocol

from report_collector.domain.models import AnalysisRequest, AnalysisResult


class AnalysisProvider(Protocol):
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult: ...
