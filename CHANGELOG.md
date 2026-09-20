# CHANGELOG

## [1.0.0] - 2026-09-20 · 첫 공개: CHANGELOG로 쌓는 개발 연혁 페이지

- `tools/build_history.py`: `surucc/suloa`·`surucc/sumz`의 `CHANGELOG.md`를 GitHub API로 받아
  `## [버전] - 날짜 · 요약` 헤더만 뽑아 `data/history.json`으로 만든다. 표준 라이브러리만 쓴다
- 공개 범위는 헤더까지. 본문을 싣지 않아 환경변수명·마이그레이션 ID 같은 내부 정보가 나가지 않는다
  (`INCLUDE_SUBHEADINGS = False`로 `### 소제목` 포함 여부를 한 줄로 바꿀 수 있게 둠)
- 화면 `index.html` + `css/style.css` + `js/app.js`: 요약 통계, 프로젝트 카드 2장,
  프로젝트 필터가 달린 월별 타임라인. 정적 HTML + ES 모듈, 빌드 도구 없음.
  밝게/어둡게 전환(시스템 설정 기본, 선택은 브라우저에 기억)
- `.github/workflows/deploy.yml`: 매일 06:00(KST)·main push·수동 실행으로 갱신 후 Pages 배포.
  비공개 저장소는 읽기 전용 토큰(`CHANGELOG_READ_TOKEN`)으로 읽는다
- 조용한 실패 금지: 수집 글자수와 파싱 건수를 단계마다 로그로 남기고, 항목이 0건이면 배포를 멈춘다.
  화면도 `history.json`을 못 읽거나 0건이면 빈 페이지 대신 오류 상자를 띄운다
- 시각은 `datetime.now(ZoneInfo("Asia/Seoul"))`. Windows에는 IANA 시간대 자료가 없어
  `tzdata`를 `requirements.txt`에 넣었다(Linux CI는 시스템 자료를 쓴다)
- 검증 중 잡은 버그 2건
  - 날짜 검증 누락: 정규식이 자릿수만 봐서 `2026-13-45` 같은 없는 날짜를 통과시켰다.
    `date.fromisoformat`으로 막음(회귀 테스트가 잡음)
  - 필터 포커스 유실: 필터를 누를 때마다 버튼을 다시 그려 키보드 포커스가 날아갔다.
    버튼은 한 번만 만들고 `aria-pressed`만 갱신하도록 고침
- 검증(2026-09-20): pytest 12건 통과. 로컬 경로·GitHub API 두 경로 모두 실행해 같은 결과 확인
  (suloa 16,755자 / 8건, sumz 19,650자 / 2건, 합 10건).
  브라우저에서 밝은·어두운 테마 표시 확인, 모바일 375px 가로 스크롤 없음·화면 밖 요소 0개,
  필터 전체 10 / SULOA 8 / SUMZ 2 및 포커스 유지 확인, 콘솔 오류 없음
