import re
from collections import Counter

from report_collector.domain.models import AnalysisRequest, AnalysisResult

TOPIC_KEYWORDS = {
    "ai-tech": ("AI", "인공지능", "디지털", "데이터", "과학기술"),
    "economy": ("경제", "금융", "재정", "물가", "투자"),
    "industry": ("산업", "무역", "공급망", "기업", "제조"),
    "labor-welfare": ("노동", "고용", "복지", "보건", "청년"),
    "education-population": ("교육", "인구", "저출생", "청소년", "대학"),
    "land-environment": ("국토", "환경", "기후", "에너지", "산불"),
    "law-security": ("법", "입법", "외교", "국방", "안보", "형사"),
}

STOP_WORDS = {
    "것으로", "대한", "위한", "통해", "관련", "보고서", "연구", "자료", "분석", "검토",
    "정책", "내용", "경우", "이후", "현재", "이번", "우리", "이러한", "있다", "한다",
    "있는", "있도록", "위해", "필요", "따라", "대해", "한다면", "한다는",
    "높은", "낮은", "결과", "부분", "필요가", "과정", "통한", "주요",
}


class ExtractiveAnalysisProvider:
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        sentences = _summary_sentences(request.text, request.title)
        topics = _topics(request.title, request.text)
        if len(sentences) < 2:
            return _unavailable(request, topics)
        return AnalysisResult(
            why_it_matters=" ".join(sentences),
            summary_kind="ANALYZED",
            key_points=sentences[:3],
            key_tags=_keywords(request.text, request.title),
            topic_candidates=topics,
            content_tag="본문 요약",
            confidence=0.8,
            evidence_pages=[],
        )


def _summary_sentences(text: str, title: str) -> list[str]:
    candidates = [
        _clean(item)
        for item in re.split(r"(?<=[.!?])\s+", _summary_window(_normalized(text), title))
    ]
    scored = [
        (index, sentence, _score(sentence, title))
        for index, sentence in enumerate(candidates)
        if _usable(sentence)
    ]
    selected: list[tuple[int, str, int]] = []
    total_length = 0
    for candidate in sorted(scored, key=lambda item: item[2], reverse=True):
        next_length = total_length + len(candidate[1]) + (1 if selected else 0)
        if next_length > 240:
            continue
        selected.append(candidate)
        total_length = next_length
        if len(selected) == 3:
            break
    return [sentence for _, sentence, _ in sorted(selected)]


def _clean(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" ·-–")
    return re.sub(r"^(?:[가-힣]\s){2}[가-힣]\s+", "", normalized)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _summary_window(text: str, title: str) -> str:
    abstract = _abstract_window(text)
    if abstract:
        return abstract
    words = [word for word in re.findall(r"[가-힣A-Za-z]{3,}", title) if word not in STOP_WORDS]
    if len(words) < 2:
        return text[:4_000]
    pattern = re.compile(r".{0,80}?".join(re.escape(word) for word in words))
    matches = list(pattern.finditer(text[:16_000]))
    if not matches:
        return text[:4_000]
    windows = [text[match.start() : match.start() + 3_000] for match in matches]
    return max(windows, key=_window_quality)


def _abstract_window(text: str) -> str | None:
    marker = re.search(r"(?:국문\s*)?(?:초록|요약|연구요약|개요)\s*", text[:16_000])
    if not marker:
        return None
    candidate = text[marker.end() : marker.end() + 3_000]
    boundary = re.search(r"(?:목차|제\s*1\s*장|Ⅰ\.|I\.)", candidate)
    return candidate[: boundary.start()] if boundary else candidate


def _usable(sentence: str) -> bool:
    blocked = ("http", "발행처", "국회입법조사처ㅣ", "자료:", "주:", "표 ")
    compact = sentence.replace(" ", "")
    return (
        40 <= len(sentence) <= 300
        and compact.endswith("다.")
        and not re.fullmatch(r"[\d.·()\- ]+", sentence)
        and not re.match(r"^\d+\)", sentence)
        and not re.match(r"^\d", sentence)
        and "ㅣ" not in sentence
        and not re.search(r"(?:\.{4,}|·{4,}|…{2,})", sentence)
        and not re.search(r"(?<![가-힣])[가-힣]\s[가-힣](?![가-힣])", sentence)
        and not any(marker in sentence for marker in blocked)
    )


def _window_quality(value: str) -> int:
    sentences = re.split(r"(?<=[.!?])\s+", value)
    prose = sum(1 for sentence in sentences if _usable(_clean(sentence)))
    noise = len(re.findall(r"(?:\.{4,}|·{4,}|…{2,})", value))
    return prose * 10 - noise * 20


def _score(sentence: str, title: str) -> int:
    signals = (
        "본 보고서", "본 연구", "본고", "그러나", "이에", "현행", "분석", "검토", "제안",
        "목적", "결과", "과제", "필요",
    )
    title_words = [word for word in re.findall(r"[가-힣A-Za-z]{2,}", title) if word not in STOP_WORDS]
    return sum(sentence.count(signal) * 4 for signal in signals) + sum(sentence.count(word) for word in title_words)


def _topics(title: str, text: str) -> list[str]:
    content = f"{title} {text[:12_000]}"
    ranked = sorted(
        ((topic, sum(content.count(keyword) for keyword in keywords)) for topic, keywords in TOPIC_KEYWORDS.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return [topic for topic, score in ranked if score > 0][:2] or ["industry"]


def _keywords(text: str, title: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z]{2,}", f"{title} {text[:12_000]}")
    counts = Counter(token for token in tokens if token not in STOP_WORDS)
    return [token for token, _ in counts.most_common(3)] or ["공식 원문"]


def _unavailable(request: AnalysisRequest, topics: list[str]) -> AnalysisResult:
    return AnalysisResult(
        why_it_matters=request.title,
        summary_kind="UNAVAILABLE",
        key_points=[request.title],
        key_tags=["공식 원문"],
        topic_candidates=topics,
        content_tag="본문 확인 필요",
        confidence=0.0,
        evidence_pages=[],
    )
