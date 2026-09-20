"""CHANGELOG 헤더 파서 회귀 테스트.

실행: .venv\\Scripts\\python.exe -m pytest tests -q
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from build_history import parse_changelog  # noqa: E402


def test_표준_헤더를_뽑는다():
    text = "# 업데이트 내역\n\n## [1.3.1] - 2026-09-20 · 레벨 변동 표시\n- 본문\n"
    (entry,) = parse_changelog(text, "t")
    assert (entry.version, entry.date, entry.summary) == ("1.3.1", "2026-09-20", "레벨 변동 표시")


def test_요약이_없어도_받는다():
    (entry,) = parse_changelog("## [1.0.0] - 2026-09-05\n", "t")
    assert entry.version == "1.0.0"
    assert entry.summary == ""


def test_요약_안의_가운뎃점은_요약에_남는다():
    (entry,) = parse_changelog("## [1.2.2] - 2026-09-12 · 벨가르딘·세르카 보정\n", "t")
    assert entry.summary == "벨가르딘·세르카 보정"


def test_본문은_싣지_않는다():
    text = "## [0.2.0] - 2026-09-20 · 첫 화면\n- SUMZ_DB_NAME 환경변수\n- 마이그레이션 fb013b28\n"
    (entry,) = parse_changelog(text, "t")
    assert "SUMZ_DB_NAME" not in entry.summary
    assert "fb013b28" not in entry.summary


def test_소제목은_직전_항목에_붙는다():
    text = "## [0.2.0] - 2026-09-20 · 첫 화면\n### 화면 디자인 개편\n### 청구서\n"
    (entry,) = parse_changelog(text, "t")
    assert entry.subheadings == ["화면 디자인 개편", "청구서"]


def test_릴리스_표시_소제목은_개수로_묶는다():
    """### PC 앱 v0.2.26 같은 번호 나열은 칩으로 늘어놓지 않는다."""
    text = (
        "## [1.2.2] - 2026-09-12 · 인식 보정\n"
        "### 화면 인식\n"
        "### PC 앱 v0.2.26\n"
        "### PC 앱 v0.2.25\n"
        "### PC 앱 v0.2.24\n"
    )
    (entry,) = parse_changelog(text, "t")
    assert entry.subheadings == ["화면 인식"]
    assert entry.releases == {"PC 앱": 3}


def test_릴리스_표시가_섞여도_작업_제목은_그대로_남는다():
    text = "## [1.0.0] - 2026-09-05 · 첫 공개\n### 앱 창: 되돌리기\n### 버전 v1 정리\n"
    (entry,) = parse_changelog(text, "t")
    # "버전 v1 정리" 는 vX.Y 로 끝나지 않으므로 작업 제목이다.
    assert entry.subheadings == ["앱 창: 되돌리기", "버전 v1 정리"]
    assert entry.releases == {}


def test_두_자리_버전_릴리스_표시도_묶인다():
    text = "## [1.0.0] - 2026-09-05 · 첫 공개\n### 런처 v1.2\n"
    (entry,) = parse_changelog(text, "t")
    assert entry.releases == {"런처": 1}
    assert entry.subheadings == []


def test_여러_항목이_파일_순서대로_나온다():
    text = "## [1.1.0] - 2026-09-06 · 나중\n## [1.0.0] - 2026-09-05 · 처음\n"
    entries = parse_changelog(text, "t")
    assert [e.version for e in entries] == ["1.1.0", "1.0.0"]


def test_형식에_어긋난_헤더는_건너뛰되_항목이_0건이면_실패한다():
    """조용한 실패 금지: 헤더는 있는데 한 건도 못 뽑으면 빌드를 멈춘다."""
    with pytest.raises(SystemExit):
        parse_changelog("## 버전 없는 제목\n", "t")


def test_다른_수준의_제목은_항목이_아니다():
    text = "# 업데이트 내역\n#### [9.9.9] - 2026-01-01 · 가짜\n## [1.0.0] - 2026-09-05 · 진짜\n"
    (entry,) = parse_changelog(text, "t")
    assert entry.version == "1.0.0"


@pytest.mark.parametrize(
    "line",
    [
        "## [1.0.0] - 2026-13-45 · 날짜가 이상함",
        "## [1.0.0] 2026-09-05 · 하이픈 없음",
        "## 1.0.0 - 2026-09-05 · 대괄호 없음",
    ],
)
def test_깨진_헤더는_항목으로_받지_않는다(line):
    with pytest.raises(SystemExit):
        parse_changelog(line + "\n", "t")


def test_실제_두_프로젝트_형식을_모두_통과한다():
    """suloa·sumz 에서 실제로 쓰이는 줄(2026-09-20 기준 복사본)."""
    real = (
        "## [1.3.1] - 2026-09-20 · 레벨·전투력 변동 표시, 카던 세팅 전투력 보정\n"
        "### 레벨·전투력 변동 표시\n"
        "## [1.0.0] - 2026-09-05 · 첫 공개\n"
        "## [0.2.0] - 2026-09-20 · 첫 화면: 렌탈 계약 등록/목록\n"
        "## [0.1.0] - 2026-09-20 · 개발 환경 세팅 (2단계)\n"
    )
    entries = parse_changelog(real, "t")
    assert len(entries) == 4
    assert entries[0].subheadings == ["레벨·전투력 변동 표시"]
    assert entries[2].summary == "첫 화면: 렌탈 계약 등록/목록"
