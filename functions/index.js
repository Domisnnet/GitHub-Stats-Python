const { onRequest } = require("firebase-functions/v2/https");
const crypto = require("crypto");
const STATS_JSON_URL = "https://raw.githubusercontent.com/Domisnnet/GitHub-Stats-Generator-Python/main/output/stats.json";

const LANG_COLORS = {
  "C": "#555555", "C++": "#f34b7d", "CSS": "#563d7c", "Cython": "#fedf5b",
  "Go": "#00ADD8", "HTML": "#e34c26", "Java": "#b07219", "JavaScript": "#f1e05a",
  "Jupyter Notebook": "#DA5B0B", "PHP": "#4F5D95", "Python": "#3572A5",
  "Ruby": "#701516", "Shell": "#89e051", "TypeScript": "#2b7489", "Vue": "#41b883", "Other": "#ededed"
};

const THEMES = {
  "tokyonight": { bg: "#1a1b27", title: "#70a5fd", text: "#a9b1d6", border: "#414868", accent: "#70a5fd", bar_bg: "#222436" },
  "dark": { bg: "#151515", title: "#ffffff", text: "#9f9f9f", border: "#e4e2e2", accent: "#ffffff", bar_bg: "#1e1e1e" },
  "dracula": { bg: "#282a36", title: "#f8f8f2", text: "#f8f8f2", border: "#44475a", accent: "#ff79c6", bar_bg: "#343746" },
  "gruvbox": { bg: "#282828", title: "#fabd2f", text: "#ebdbb2", border: "#504945", accent: "#fabd2f", bar_bg: "#32302f" },
  "onedark": { bg: "#282c34", title: "#61afef", text: "#abb2bf", border: "#3e4451", accent: "#61afef", bar_bg: "#21252b" }
};

function makeEtag(svg) {
  return crypto.createHash("md5").update(svg).digest("hex");
}

function renderLangBars(langsObj, centerX, startY, maxWidth, theme) {
  const langsArray = Object.entries(langsObj);
  const total = langsArray.reduce((sum, [, val]) => sum + val, 0);

  if (total === 0) {
    return `<text x="${centerX}" y="${startY}" fill="${theme.text}" text-anchor="middle" font-size="14">No language data available.</text>`;
  }

  const top = langsArray.sort((a, b) => b[1] - a[1]).slice(0, 5);
  let y = startY;
  const gap = 26;
  const barH = 10;
  const left = centerX - (maxWidth / 2);
  let svg = "";

  top.forEach(([lang, val], i) => {
    const pct = (val / total) * 100;
    const width = maxWidth * (pct / 100);
    const color = LANG_COLORS[lang] || LANG_COLORS["Other"];
    const delay = 0.2 + (i * 0.15);
    svg += `
<text x="${left - 12}" y="${y}" fill="${theme.text}" font-size="12" text-anchor="end">${lang}</text>
<rect x="${left}" y="${y - 9}" width="${maxWidth}" height="${barH}" rx="5" fill="${theme.bar_bg}"/>
<rect x="${left}" y="${y - 9}" width="0" height="${barH}" rx="5" fill="${color}">
  <animate attributeName="width" from="0" to="${width}" dur="0.8s" begin="${delay}s" fill="freeze"/>
</rect>
<text x="${left + maxWidth + 10}" y="${y}" fill="${theme.text}" font-size="12">${pct.toFixed(1)}%</text>`;
    y += gap;
  });

  return svg;
}

function buildCombinedSvg(user, langs, theme) {
  const userName = user.name || user.login || "GitHub User"; 
  return `
<svg viewBox="0 0 900 380" xmlns="http://www.w3.org/2000/svg" opacity="0">
<style>.stat-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }</style>
<animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>
<rect width="100%" height="100%" rx="28" fill="${theme.bg}" stroke="${theme.border}" stroke-width="4"/>
<defs>
  <radialGradient id="logoAura" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="${theme.accent}" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="${theme.accent}" stop-opacity="0"/>
  </radialGradient>
</defs>
<circle cx="90" cy="95" r="48" fill="url(#logoAura)">
  <animate attributeName="opacity" from="0.35" to="0.65" dur="2.4s" repeatCount="indefinite"/>
</circle>
<circle cx="90" cy="95" r="34" fill="${theme.bar_bg}"/>
<circle cx="90" cy="95" r="34" fill="none" stroke="${theme.accent}" stroke-width="4"/>
<text x="90" y="106" text-anchor="middle" fill="${theme.accent}" font-size="30" font-weight="bold" letter-spacing="5">&lt;/&gt;</text>
<text x="160" y="68" fill="${theme.title}" font-size="22" font-weight="bold">${userName} · Developer Dashboard</text>
<text x="160" y="92" fill="${theme.text}" font-size="13">Da faísca da ideia à Constelação do código.</text>
<text x="160" y="112" fill="${theme.text}" font-size="13">Construindo um Universo de possibilidades!!</text>
<text x="160" y="145" fill="${theme.text}" font-size="13">📦 ${user.total_repos} Repositórios · ⭐ ${user.total_stars} Stars · 📊 ${user.total_commits_year} Commits/ano · 🧠 ${Object.keys(langs).length} Linguagens</text>
<circle cx="825" cy="95" r="46" fill="none" stroke="#2a2a2a" stroke-width="7"/>
<circle cx="825" cy="95" r="46" fill="none" stroke="${theme.accent}" stroke-width="7" stroke-dasharray="290" stroke-dashoffset="290" transform="rotate(-90 825 95)">
  <animate attributeName="stroke-dashoffset" from="290" to="30" dur="1.4s" fill="freeze"/>
</circle>
<text x="825" y="112" text-anchor="middle" fill="${theme.accent}" font-size="34" font-weight="bold">A</text>
<text x="450" y="210" text-anchor="middle" fill="${theme.accent}" font-size="16" font-weight="bold">Top Languages</text>
${renderLangBars(langs, 450, 240, 360, theme)}
</svg>`;
}

exports.statsSvg = onRequest({ maxInstances: 10 }, async (req, res) => {
  const username = req.query.username || "Domisnnet";
  const themeName = req.query.theme || "tokyonight";
  const theme = THEMES[themeName] || THEMES["tokyonight"];
  try {
    const response = await fetch(STATS_JSON_URL);
    if (!response.ok) throw new Error("Falha ao buscar stats.json");
    const data = await response.json();
    const user = {
      name: username,
      login: username,
      total_repos: data.total_repos || 0,
      total_commits_year: data.total_commits_year || 0,
      total_stars: data.total_stars || 0
    };
    const svg = buildCombinedSvg(user, data.top_languages || {}, theme);
    const etag = makeEtag(svg);
    if (req.headers["if-none-match"] === etag) {
      return res.status(304).end();
    }
    res.set({
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
      "ETag": etag
    });
    res.status(200).send(svg);
  } catch (error) {
    console.error("Erro ao gerar SVG:", error);
    res.status(500).send("Erro ao carregar estatísticas.");
  }
});