import os

import httpx
from report_collector.domain.models import AnalysisRequest, AnalysisResult
from report_collector.providers.ai.base import AnalysisProvider
from report_collector.providers.ai.extractive_provider import ExtractiveAnalysisProvider
from report_collector.providers.ai.openai_provider import OpenAIAnalysisProvider


class FallbackAnalysisProvider:
    def __init__(self, primary: AnalysisProvider, fallback: AnalysisProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        try:
            return await self.primary.analyze(request)
        except (httpx.HTTPError, ValueError):
            return await self.fallback.analyze(request)


def build_analysis_provider() -> AnalysisProvider:
    provider_name = os.getenv("ANALYSIS_PROVIDER", "extractive").strip().lower()
    api_key = os.getenv("ANALYSIS_API_KEY", "").strip()
    fallback = ExtractiveAnalysisProvider()
    if provider_name != "openai" or not api_key:
        return fallback
    primary = OpenAIAnalysisProvider(
        api_key=api_key,
        model=os.getenv("ANALYSIS_MODEL", "gpt-5-mini"),
        endpoint=os.getenv("OPENAI_RESPONSES_URL", "https://api.openai.com/v1/responses"),
    )
    return FallbackAnalysisProvider(primary, fallback)
