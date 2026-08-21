import re

from report_collector.domain.models import AnalysisRequest, AnalysisResult

TOPIC_KEYWORDS = {
    "ai-tech": ("AI", "인공지능", "디지털", "과학기술"),
    "economy": ("경제", "금융", "재정", "물가"),
    "industry": ("산업", "무역", "공급망", "기업"),
    "labor-welfare": ("노동", "고용", "복지", "보건"),
    "education-population": ("교육", "인구", "저출생", "청소년"),
    "land-environment": ("국토", "환경", "기후", "에너지"),
    "law-security": ("법", "외교", "국방", "안보"),
}

TOPIC_TAGS = {
    "ai-tech": ["AI 책임", "검증 기준", "공공 도입"],
    "economy": ["경기 전망", "물가", "재정"],
    "industry": ["공급망", "제조업", "정책 대응"],
    "labor-welfare": ["고용", "복지", "노동시장"],
    "education-population": ["교육", "인구", "청년"],
    "land-environment": ["국토", "환경", "기후"],
    "law-security": ["법제", "외교", "안보"],
}


class MockAnalysisProvider:
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        combined = f"{request.title} {request.text}"
        scored = [
            (topic, sum(combined.count(keyword) for keyword in keywords))
            for topic, keywords in TOPIC_KEYWORDS.items()
        ]
        selected = [
            topic
            for topic, score in sorted(scored, key=lambda item: item[1], reverse=True)
            if score > 0
        ][:2] or ["industry"]
        sentences = [
            part.strip()
            for part in re.split(r"(?<=[.!?다])\s+|\n+", request.text)
            if len(part.strip()) >= 12
        ]
        points = [sentence[:180] for sentence in sentences[:3]] or [
            f"{request.title}의 주요 내용을 관리자 검수용으로 정리했습니다."[:180]
        ]
        evidence = list(range(1, min(request.page_count or 1, len(points)) + 1))
        return AnalysisResult(
            why_it_matters=f"{request.institution}이 공개한 {request.title}의 핵심 쟁점을 빠르게 확인할 수 있습니다."[:240],
            summary_kind="UNAVAILABLE",
            key_points=points,
            key_tags=TOPIC_TAGS[selected[0]],
            topic_candidates=selected,
            content_tag="주요 분석",
            confidence=0.5,
            evidence_pages=evidence,
        )
