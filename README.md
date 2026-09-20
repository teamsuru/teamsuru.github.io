# TEAMSURU

개발 연혁을 쌓아 두고 남에게 보여주는 공개 페이지. <https://teamsuru.github.io>

각 프로젝트의 `CHANGELOG.md`에서 **버전·날짜·한줄요약(`## [버전] - 날짜 · 요약` 헤더)** 만 뽑아
타임라인으로 쌓는다. 본문은 싣지 않으므로 환경변수명·마이그레이션 ID 같은 내부 정보가 공개되지 않는다.

- 회사 업무로 만든 것은 싣지 않는다.
- 연혁은 손으로 적지 않는다. 각 프로젝트에서 CHANGELOG를 쓰면 다음 갱신 때 저절로 올라온다.

## 어떻게 돌아가나

```
surucc/suloa  CHANGELOG.md ─┐
                            ├─> tools/build_history.py ─> data/history.json ─> index.html
surucc/sumz   CHANGELOG.md ─┘        (GitHub Actions)                            (GitHub Pages)
```

`.github/workflows/deploy.yml`이 **매일 06:00(KST)** 와 main 브랜치 push, 그리고 Actions 탭의
수동 실행 버튼으로 돈다. 소스 저장소가 비공개라 읽기 전용 토큰을 하나 쓴다.

## 파일

| 경로 | 용도 |
|---|---|
| `index.html` `css/` `js/` | 화면 (정적 HTML + ES 모듈, 빌드 도구 없음) |
| `tools/build_history.py` | CHANGELOG 수집·파싱 -> `data/history.json` (표준 라이브러리만 사용) |
| `tests/test_parse.py` | 헤더 파서 회귀 테스트 |
| `.github/workflows/deploy.yml` | 갱신 + Pages 배포 |
| `data/history.json` | 빌드 산출물. 커밋하지 않는다 (`.gitignore`) |

## 로컬에서 띄우기

ES 모듈 + `fetch`라 `file://`로는 안 열린다. 아무 정적 서버면 된다.

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 내 PC에 있는 저장소에서 바로 읽기 (토큰 불필요)
.venv\Scripts\python.exe tools/build_history.py ^
  --local suloa=D:/work/game/suloa/CHANGELOG.md ^
  --local sumz=D:/work/sumz/maru/CHANGELOG.md

python -m http.server 8788
```

GitHub에서 받아오는 경로를 확인하려면 (토큰을 화면에 찍지 않는다):

```powershell
$env:GITHUB_TOKEN = (gh auth token); .venv\Scripts\python.exe tools/build_history.py; $env:GITHUB_TOKEN = ""
```

테스트:

```bash
.venv\Scripts\python.exe -m pytest tests -q
```

## 프로젝트 추가하기

`tools/build_history.py` 맨 위 `PROJECTS` 목록에 한 덩이를 더 적는다. 색을 따로 주려면
`css/style.css`의 `--proj-<key>` / `--proj-<key>-soft`와 `js/app.js`의 `TONES`에 같은 키를 추가한다.
(색을 안 넣으면 기본 강조색으로 나온다.)

새 저장소가 비공개라면 아래 토큰의 접근 저장소 목록에도 그 저장소를 추가해야 한다.

## 최초 설정 (한 번만)

1. **저장소** — `teamsuru` 조직에 `teamsuru.github.io` 이름으로 공개 저장소를 만든다.
   (이름이 `<계정>.github.io`여야 주소가 `https://teamsuru.github.io`가 된다.)
2. **읽기 전용 토큰** — <https://github.com/settings/personal-access-tokens/new>
   - Resource owner: `surucc` (비공개 저장소의 주인)
   - Repository access: Only select repositories -> `suloa`, `sumz`
   - Permissions: Repository permissions > **Contents: Read-only** 하나만
   - Expiration은 1년. 만료되면 Actions가 빨갛게 실패하므로 조용히 멈추지 않는다.
3. **토큰 등록** — 이 저장소 Settings > Secrets and variables > Actions > New repository secret
   - Name: `CHANGELOG_READ_TOKEN`, Secret: 위에서 만든 토큰
4. **Pages 켜기** — Settings > Pages > Build and deployment > Source: **GitHub Actions**

## 갱신이 안 될 때

Actions 탭에서 실패한 실행을 연다. 빌드는 실패를 감추지 않으므로 로그에 이유가 그대로 남는다.

| 증상 | 원인 |
|---|---|
| `GITHUB_TOKEN 이 없습니다` | 시크릿 `CHANGELOG_READ_TOKEN` 미등록 또는 이름 오타 |
| `조회 실패: HTTP 404` / `403` | 토큰 만료, 또는 토큰의 접근 저장소 목록에 그 저장소가 빠짐 |
| `항목이 0건입니다` | CHANGELOG 헤더 형식이 `## [버전] - YYYY-MM-DD · 요약` 에서 벗어남 |
| `형식에 맞지 않는 헤더를 건너뜀` (경고) | 그 줄만 빠지고 나머지는 올라감. 헤더를 고치면 된다 |
