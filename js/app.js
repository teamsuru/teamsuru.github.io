// TEAMSURU 개발 연혁 - data/history.json 을 읽어 화면을 그린다.

const DATA_URL = "data/history.json";
const THEME_KEY = "teamsuru.theme";
const FILTER_ALL = "all";

// 프로젝트별 색. style.css 의 --proj-* 와 짝을 이룬다.
const TONES = {
  suloa: ["var(--proj-suloa)", "var(--proj-suloa-soft)"],
  sumz: ["var(--proj-sumz)", "var(--proj-sumz-soft)"],
};

const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
};

const toneVars = (key) => {
  const [tone, soft] = TONES[key] ?? ["var(--accent)", "var(--accent-soft)"];
  return `--tone:${tone};--tone-soft:${soft};`;
};

/* ---------- 테마 ---------- */

function initTheme() {
  const toggle = document.getElementById("theme-toggle");
  let stored = null;
  try {
    stored = localStorage.getItem(THEME_KEY);
  } catch {
    // 사생활 보호 모드 등에서 막힐 수 있다. 그 경우 시스템 설정을 따른다.
  }
  if (stored === "dark" || stored === "light") {
    document.documentElement.dataset.theme = stored;
  }

  toggle.addEventListener("click", () => {
    const isDark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      // 저장에 실패해도 이번 방문에는 적용된다.
    }
  });
}

/* ---------- 표기 ---------- */

const fmtDate = (iso) => {
  const [y, m, d] = iso.split("-");
  return `${y}.${m}.${d}`;
};

const monthLabel = (iso) => {
  const [y, m] = iso.split("-");
  return `${y}년 ${Number(m)}월`;
};

function daysSince(iso) {
  const then = new Date(`${iso}T00:00:00+09:00`);
  const diff = Date.now() - then.getTime();
  return Math.max(0, Math.floor(diff / 86_400_000));
}

function freshness(iso) {
  const days = daysSince(iso);
  if (days === 0) return "오늘";
  if (days === 1) return "어제";
  if (days < 30) return `${days}일 전`;
  if (days < 365) return `${Math.floor(days / 30)}개월 전`;
  return `${Math.floor(days / 365)}년 전`;
}

/* ---------- 그리기 ---------- */

function renderStats(data) {
  const latest = data.entries[0]?.date;
  // suffixClass: "unit" = 숫자에 바로 붙는 단위(2개), "note" = 띄어 쓰는 덧붙임(오늘)
  const rows = [
    ["프로젝트", String(data.projects.length), "개", "unit"],
    ["릴리스", String(data.entries.length), "회", "unit"],
    ["최근 업데이트", latest ? fmtDate(latest) : "-", latest ? freshness(latest) : "", "note"],
  ];

  const stats = document.getElementById("stats");
  stats.replaceChildren(
    ...rows.map(([label, value, suffix, suffixClass]) => {
      const box = el("div", "stat");
      box.append(el("dt", null, label));
      const dd = el("dd", null, value);
      if (suffix) dd.append(el("span", suffixClass, suffix));
      box.append(dd);
      return box;
    })
  );
}

function renderProjects(projects) {
  const grid = document.getElementById("projects");
  grid.replaceChildren(
    ...projects.map((p) => {
      const card = el("article", "project-card");
      card.setAttribute("style", toneVars(p.key));

      const top = el("div", "project-top");
      top.append(el("h3", "project-name", p.name), el("span", "version-pill", `v${p.latest_version}`));

      const tech = el("ul", "tech-list");
      tech.append(...p.tech.map((t) => el("li", null, t)));

      const foot = el("div", "project-foot");
      foot.append(el("span", null, `릴리스 ${p.release_count}회 · ${fmtDate(p.first_date)} 시작`));
      if (p.site) {
        const link = el("a", "project-link", p.site.replace(/^https?:\/\//, ""));
        link.href = p.site;
        link.target = "_blank";
        link.rel = "noopener";
        foot.append(link);
      }

      card.append(top, el("p", "project-tagline", p.tagline), el("p", "project-desc", p.description), tech, foot);
      return card;
    })
  );
}

/** 버튼은 한 번만 만든다. 누를 때마다 다시 그리면 키보드 포커스가 날아간다.
 *  현재 선택을 표시하는 함수를 돌려준다. */
function renderFilters(projects, onChange) {
  const box = document.getElementById("filters");
  const options = [{ key: FILTER_ALL, name: "전체" }, ...projects];

  const buttons = options.map((opt) => {
    const btn = el("button", "filter-btn", opt.name);
    btn.type = "button";
    btn.dataset.key = opt.key;
    if (opt.key !== FILTER_ALL) btn.setAttribute("style", toneVars(opt.key));
    btn.addEventListener("click", () => onChange(opt.key));
    return btn;
  });
  box.replaceChildren(...buttons);

  return (current) => {
    for (const btn of buttons) {
      btn.setAttribute("aria-pressed", String(btn.dataset.key === current));
    }
  };
}

function renderTimeline(entries, projectNames) {
  const list = document.getElementById("timeline");
  const empty = document.getElementById("timeline-empty");
  list.replaceChildren();
  empty.hidden = entries.length > 0;

  let lastMonth = null;
  for (const entry of entries) {
    const month = entry.date.slice(0, 7);
    if (month !== lastMonth) {
      list.append(el("li", "month-divider", monthLabel(entry.date)));
      lastMonth = month;
    }

    const item = el("li", "entry");
    item.setAttribute("style", toneVars(entry.project));

    const top = el("div", "entry-top");
    top.append(
      el("span", "entry-project", projectNames[entry.project] ?? entry.project),
      el("span", "entry-version", `v${entry.version}`)
    );

    const body = el("div", "entry-body");
    const summary = el("p", "entry-summary", entry.summary || "(요약 없음)");
    if (!entry.summary) summary.classList.add("is-empty");
    body.append(top, summary);

    const releases = Object.entries(entry.releases ?? {});
    if (entry.subheadings?.length || releases.length) {
      const subs = el("ul", "sub-list");
      subs.append(...(entry.subheadings ?? []).map((s) => el("li", null, s)));
      // "PC 앱 v0.2.26" 같은 릴리스 표시는 하나씩 늘어놓지 않고 개수로 묶는다.
      subs.append(...releases.map(([label, n]) => el("li", "sub-count", `${label} 릴리스 ${n}회`)));
      body.append(subs);
    }

    item.append(el("div", "entry-date", fmtDate(entry.date)), body);
    list.append(item);
  }
}

function showError(detail) {
  document.getElementById("loading").hidden = true;
  document.getElementById("error").hidden = false;
  document.getElementById("error-detail").textContent = detail;
  console.error("[teamsuru]", detail);
}

/* ---------- 시작 ---------- */

async function main() {
  initTheme();

  let data;
  try {
    const res = await fetch(DATA_URL, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${DATA_URL} 응답 ${res.status}`);
    data = await res.json();
  } catch (e) {
    showError(String(e.message ?? e));
    return;
  }

  // 빈 결과를 정상처럼 보여주지 않는다.
  if (!data?.entries?.length || !data?.projects?.length) {
    showError("기록이 0건입니다. 빌드(tools/build_history.py)가 제대로 돌았는지 확인이 필요합니다.");
    return;
  }

  document.getElementById("loading").hidden = true;

  const projectNames = Object.fromEntries(data.projects.map((p) => [p.key, p.name]));
  renderStats(data);
  renderProjects(data.projects);

  let markPressed;
  const applyFilter = (next) => {
    markPressed(next);
    renderTimeline(
      next === FILTER_ALL ? data.entries : data.entries.filter((e) => e.project === next),
      projectNames
    );
  };
  markPressed = renderFilters(data.projects, applyFilter);
  applyFilter(FILTER_ALL);

  if (data.generated_at) {
    const at = data.generated_at.slice(0, 16).replace("T", " ");
    document.getElementById("generated").textContent =
      `각 프로젝트의 CHANGELOG에서 하루 한 번 자동으로 갱신됩니다. 마지막 갱신 ${at} (KST)`;
  }
}

main();
