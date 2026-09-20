"""배포 폴더 해시 붙이기 회귀 테스트.

실행: .venv\\Scripts\\python.exe -m pytest tests -q
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from stamp_assets import stamp  # noqa: E402

HTML = (
    '<link rel="stylesheet" href="https://cdn.example.com/font.css">\n'
    '<link rel="stylesheet" href="css/style.css">\n'
    '<link rel="icon" href="favicon.svg">\n'
    '<script type="module" src="js/app.js"></script>\n'
)


@pytest.fixture
def site(tmp_path: Path) -> Path:
    (tmp_path / "css").mkdir()
    (tmp_path / "js").mkdir()
    (tmp_path / "css" / "style.css").write_text("body{color:red}", encoding="utf-8")
    (tmp_path / "js" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "index.html").write_text(HTML, encoding="utf-8")
    return tmp_path


def read(site: Path) -> str:
    return (site / "index.html").read_text(encoding="utf-8")


def test_css_와_js_에만_해시가_붙는다(site):
    assert stamp(site) == 2
    html = read(site)
    assert re.search(r'href="css/style\.css\?v=[0-9a-f]{8}"', html)
    assert re.search(r'src="js/app\.js\?v=[0-9a-f]{8}"', html)


def test_외부_CDN_과_favicon_은_건드리지_않는다(site):
    stamp(site)
    html = read(site)
    assert 'href="https://cdn.example.com/font.css"' in html
    assert 'href="favicon.svg"' in html


def test_내용이_바뀌면_해시도_바뀐다(site):
    stamp(site)
    before = re.search(r'js/app\.js\?v=([0-9a-f]{8})', read(site)).group(1)

    (site / "index.html").write_text(HTML, encoding="utf-8")
    (site / "js" / "app.js").write_text("console.log(2)", encoding="utf-8")
    stamp(site)
    after = re.search(r'js/app\.js\?v=([0-9a-f]{8})', read(site)).group(1)

    assert before != after


def test_내용이_같으면_해시도_같다(site):
    stamp(site)
    first = read(site)
    (site / "index.html").write_text(HTML, encoding="utf-8")
    stamp(site)
    assert read(site) == first


def test_참조한_파일이_없으면_배포를_멈춘다(site):
    """조용한 실패 금지: 깨진 참조를 그대로 올리지 않는다."""
    (site / "js" / "app.js").unlink()
    with pytest.raises(SystemExit):
        stamp(site)


def test_붙일_주소가_하나도_없으면_멈춘다(tmp_path):
    (tmp_path / "index.html").write_text("<p>없음</p>", encoding="utf-8")
    with pytest.raises(SystemExit):
        stamp(tmp_path)


def test_index_가_없으면_멈춘다(tmp_path):
    with pytest.raises(SystemExit):
        stamp(tmp_path)
