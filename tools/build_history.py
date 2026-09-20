"""각 프로젝트의 CHANGELOG.md 를 읽어 타임라인 데이터(data/history.json)를 만든다.

저장소가 비공개라서 기본 경로는 GitHub API + 읽기 전용 토큰이다.
로컬 사본으로 확인할 때는 --local 로 경로를 직접 준다.

실행 예:
    GITHUB_TOKEN=<읽기전용토큰> python tools/build_history.py
    python tools/build_history.py --local suloa=D:/work/game/suloa/CHANGELOG.md

CHANGELOG 헤더 형식(~/AI_rules/suru.md 규칙):
    ## [버전] - YYYY-MM-DD · 한줄요약
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# 사이트에 싣는 프로젝트. 회사 업무로 만든 것은 여기 넣지 않는다.
PROJECTS: list[dict] = [
    {
        "key": "suloa",
        "name": "SULOA",
        "tagline": "로스트아크 공격대 숙제표",
        "description": (
            "일일·주간 숙제를 여러 명이 링크 하나로 같이 체크하는 웹. "
            "계정 없이 방 주소만 알면 쓰고, 게임 화면을 읽어 숙제를 자동으로 채우는 PC 앱도 같이 만듭니다."
        ),
        "repo": "surucc/suloa",
        "changelog_path": "CHANGELOG.md",
        "site": "https://suloa.kr",
        "tech": ["JavaScript", "Firebase RTDB", "Cloudflare Workers", "PWA", "Windows 앱"],
    },
    {
        "key": "sumz",
        "name": "SUMZ",
        "tagline": "렌탈·물류·인사 통합 업무 시스템",
        "description": (
            "계약 체결부터 청구·재고까지 한 포털에서 다루는 자체 업무 시스템. "
            "문서번호 채번, 상태 전이, 청구 계산 같은 업무 규칙을 DB 제약과 회귀 테스트로 못 박아 둡니다."
        ),
        "repo": "surucc/sumz",
        "changelog_path": "CHANGELOG.md",
        "site": None,
        "tech": ["Python", "FastAPI", "PostgreSQL", "Alembic", "pytest"],
    },
]

# ### 소제목까지 싣는다(제목만. 본문은 어느 쪽이든 싣지 않는다).
# False 로 바꾸면 버전·날짜·한줄요약만 남는다.
INCLUDE_SUBHEADINGS = True

# ## [1.3.1] - 2026-09-20 · 레벨·전투력 변동 표시
#    구분자는 가운뎃점 U+00B7. 요약이 없는 옛 항목도 허용한다.
HEADER_RE = re.compile(
    r"^##\s*\[(?P<version>[^\]]+)\]\s*-\s*(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:\s*[\u00b7\u2022]\s*(?P<summary>.+?))?\s*$"
)
SUBHEADER_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")

# "### PC 앱 v0.2.26" 처럼 릴리스를 표시하는 소제목. 작업 제목이 아니라 번호 나열이라
# 하나씩 늘어놓지 않고 "PC 앱 릴리스 19회" 로 묶는다(SULOA 1.2.2 에 19개가 붙어 있다).
RELEASE_SUBHEADER_RE = re.compile(r"^(?P<label>.+?)\s+v\d+\.\d+(?:\.\d+)?$")

GITHUB_API = "https://api.github.com/repos/{repo}/contents/{path}"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "history.json"


@dataclass
class Entry:
    project: str
    version: str
    date: str
    summary: str
    subheadings: list[str] = field(default_factory=list)
    releases: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        out = {
            "project": self.project,
            "version": self.version,
            "date": self.date,
            "summary": self.summary,
        }
        if INCLUDE_SUBHEADINGS:
            if self.subheadings:
                out["subheadings"] = self.subheadings
            if self.releases:
                out["releases"] = self.releases
        return out


def parse_changelog(text: str, project_key: str) -> list[Entry]:
    """CHANGELOG 본문에서 ## 헤더를 뽑는다. 본문 내용은 싣지 않는다."""
    entries: list[Entry] = []
    heading_lines = 0
    for line in text.splitlines():
        if line.startswith("## "):
            heading_lines += 1
            m = HEADER_RE.match(line)
            if not m:
                # 규칙에서 벗어난 헤더는 버리지 말고 드러낸다.
                print(f"  [경고] {project_key}: 형식에 맞지 않는 헤더를 건너뜀: {line!r}")
                continue
            try:
                # 정규식은 자릿수만 본다. 2026-13-45 같은 없는 날짜를 여기서 거른다.
                date.fromisoformat(m.group("date"))
            except ValueError:
                print(f"  [경고] {project_key}: 없는 날짜라 건너뜀: {line!r}")
                continue
            entries.append(
                Entry(
                    project=project_key,
                    version=m.group("version"),
                    date=m.group("date"),
                    summary=(m.group("summary") or "").strip(),
                )
            )
        elif entries and (m := SUBHEADER_RE.match(line)):
            title = m.group("title")
            if rel := RELEASE_SUBHEADER_RE.match(title):
                label = rel.group("label")
                entries[-1].releases[label] = entries[-1].releases.get(label, 0) + 1
            else:
                entries[-1].subheadings.append(title)

    subs = sum(len(e.subheadings) for e in entries)
    rels = sum(sum(e.releases.values()) for e in entries)
    print(
        f"  {project_key}: ## 헤더 {heading_lines}줄 -> 항목 {len(entries)}건 파싱"
        f" (소제목 {subs}개, 릴리스 표시 {rels}개는 묶음)"
    )
    if heading_lines and not entries:
        raise SystemExit(f"[오류] {project_key}: 헤더는 {heading_lines}줄인데 파싱된 항목이 0건입니다.")
    return entries


def fetch_changelog(repo: str, path: str, token: str) -> str:
    """GitHub API 로 파일 본문을 받는다. 실패는 그대로 드러낸다(빈 문자열 반환 금지)."""
    req = urllib.request.Request(
        GITHUB_API.format(repo=repo, path=path),
        headers={
            "Accept": "application/vnd.github.raw+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "teamsuru-history-builder",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        hint = ""
        if e.code in (403, 404):
            hint = " (토큰에 해당 저장소 Contents 읽기 권한이 있는지 확인하세요)"
        raise SystemExit(f"[오류] {repo}/{path} 조회 실패: HTTP {e.code}{hint}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"[오류] {repo}/{path} 조회 실패: {e.reason}") from e


def load_sources(local_overrides: dict[str, str]) -> dict[str, str]:
    """프로젝트별 CHANGELOG 본문을 모은다."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    texts: dict[str, str] = {}
    for project in PROJECTS:
        key = project["key"]
        if key in local_overrides:
            path = Path(local_overrides[key])
            if not path.is_file():
                raise SystemExit(f"[오류] {key}: 로컬 파일이 없습니다: {path}")
            text = path.read_text(encoding="utf-8")
            print(f"  {key}: 로컬 {path} 에서 {len(text):,}자 읽음")
        else:
            if not token:
                raise SystemExit(
                    "[오류] 환경변수 GITHUB_TOKEN 이 없습니다. "
                    "비공개 저장소를 읽으려면 읽기 전용 토큰이 필요합니다."
                )
            text = fetch_changelog(project["repo"], project["changelog_path"], token)
            print(f"  {key}: {project['repo']} 에서 {len(text):,}자 받음")
        texts[key] = text
    return texts


def build(texts: dict[str, str]) -> dict:
    all_entries: list[Entry] = []
    project_rows: list[dict] = []

    for project in PROJECTS:
        key = project["key"]
        entries = parse_changelog(texts[key], key)
        if not entries:
            raise SystemExit(f"[오류] {key}: 항목이 0건입니다. CHANGELOG 형식을 확인하세요.")

        # 날짜 내림차순, 같은 날짜면 버전 내림차순(파일에 적힌 순서가 곧 최신순이라 안정 정렬로 충분)
        dates = sorted(e.date for e in entries)
        project_rows.append(
            {
                **{k: project[k] for k in ("key", "name", "tagline", "description", "site", "tech")},
                "latest_version": entries[0].version,
                "latest_date": entries[0].date,
                "first_date": dates[0],
                "release_count": len(entries),
            }
        )
        all_entries.extend(entries)

    all_entries.sort(key=lambda e: e.date, reverse=True)
    print(f"  합계: 프로젝트 {len(project_rows)}개 / 항목 {len(all_entries)}건")

    return {
        "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "projects": project_rows,
        "entries": [e.as_dict() for e in all_entries],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CHANGELOG -> data/history.json 빌드")
    parser.add_argument(
        "--local",
        action="append",
        default=[],
        metavar="KEY=PATH",
        help="해당 프로젝트를 로컬 파일에서 읽는다 (예: --local suloa=D:/work/game/suloa/CHANGELOG.md)",
    )
    args = parser.parse_args()

    overrides: dict[str, str] = {}
    known = {p["key"] for p in PROJECTS}
    for item in args.local:
        if "=" not in item:
            raise SystemExit(f"[오류] --local 형식은 KEY=PATH 입니다: {item!r}")
        key, path = item.split("=", 1)
        if key not in known:
            raise SystemExit(f"[오류] 모르는 프로젝트 키: {key} (가능: {', '.join(sorted(known))})")
        overrides[key] = path

    print("[1/3] CHANGELOG 수집")
    texts = load_sources(overrides)

    print("[2/3] 헤더 파싱")
    data = build(texts)

    print("[3/3] 저장")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  {OUT_PATH} 기록 완료 ({OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
