"""배포 폴더의 index.html 에서 css/js 주소 뒤에 내용 해시를 붙인다.

GitHub Pages 는 index.html 과 js/css 에 각각 `Cache-Control: max-age=600` 을 준다.
둘이 따로 만료되므로, 배포 직후 **새 HTML 에 옛 JS 가 물리는** 구간이 생긴다
(2026-09-20 실측: 새 app.js 가 서버에 올라갔는데 브라우저는 옛 app.js 를 써서
묶음 칩이 안 나왔다). 주소에 내용 해시를 붙이면 파일이 바뀔 때 주소도 바뀌어,
index.html 만 새로 받으면 나머지도 반드시 새 것을 받는다.

실행: python tools/stamp_assets.py _site
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

# 같은 폴더에 올라가는 파일만 대상. 외부 CDN 주소(https://...)는 건드리지 않는다.
ASSET_RE = re.compile(r'(?P<attr>href|src)="(?P<path>(?:css|js)/[^"?]+)"')
HASH_LEN = 8


def stamp(site: Path) -> int:
    """index.html 을 제자리에서 고치고, 손본 주소 개수를 돌려준다."""
    index = site / "index.html"
    if not index.is_file():
        raise SystemExit(f"[오류] {index} 가 없습니다.")

    stamped: list[str] = []

    def repl(m: re.Match[str]) -> str:
        rel = m.group("path")
        target = site / rel
        if not target.is_file():
            # 조용한 실패 금지: 참조가 깨진 채 배포하지 않는다.
            raise SystemExit(f"[오류] index.html 이 가리키는 {rel} 파일이 없습니다.")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()[:HASH_LEN]
        stamped.append(f"{rel}?v={digest}")
        return f'{m.group("attr")}="{rel}?v={digest}"'

    html = ASSET_RE.sub(repl, index.read_text(encoding="utf-8"))

    if not stamped:
        raise SystemExit("[오류] 손본 주소가 0개입니다. index.html 의 css/js 참조를 확인하세요.")

    index.write_text(html, encoding="utf-8")
    for s in stamped:
        print(f"  {s}")
    return len(stamped)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("사용법: python tools/stamp_assets.py <배포폴더>")
    site = Path(sys.argv[1])
    if not site.is_dir():
        raise SystemExit(f"[오류] 폴더가 없습니다: {site}")
    print(f"[해시 붙이기] {site}")
    print(f"  총 {stamp(site)}개 주소에 붙였습니다.")


if __name__ == "__main__":
    main()
