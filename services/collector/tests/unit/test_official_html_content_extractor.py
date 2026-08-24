from bs4 import BeautifulSoup
from report_collector.services.official_html_content_extractor import (
    extract_official_html_content,
)


def test_extracts_common_official_body_without_download_noise() -> None:
    soup = BeautifulSoup(
        """
        <html><body>
          <div class="bbs_v_cont">
            <p>정부는 지역 산업의 생산성 향상과 고용 확대를 위해 지원 체계를 강화합니다.</p>
            <p>현장 수요를 반영해 관계 기관의 협업과 후속 점검도 이어갈 계획입니다.</p>
            <a class="download">첨부파일 내려받기</a>
          </div>
        </body></html>
        """,
        "html.parser",
    )

    content = extract_official_html_content(soup)

    assert content is not None
    assert "생산성 향상" in content
    assert "첨부파일" not in content


def test_falls_back_to_readable_paragraphs() -> None:
    soup = BeautifulSoup(
        """
        <html><body>
          <div><p>새로운 정책은 현장 의견을 반영해 단계적으로 시행합니다.</p></div>
          <div><p>관계 기관은 세부 지침과 지원 방안을 함께 안내할 예정입니다.</p></div>
        </body></html>
        """,
        "html.parser",
    )

    content = extract_official_html_content(soup)

    assert content is not None
    assert "관계 기관" in content
