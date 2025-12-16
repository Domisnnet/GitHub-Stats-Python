import os
import sys
import time
import requests
from datetime import datetime
from collections import defaultdict

# =========================
# CONFIGURAÇÕES
# =========================

GITHUB_API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}" if TOKEN else None,
}

SESSION = requests.Session()
SESSION.headers.update({k: v for k, v in HEADERS.items() if v})

# =========================
# CORES DAS LINGUAGENS
# =========================

LANG_COLORS = {
    "Python": "#00f5a0",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "C": "#555555",
    "C++": "#f34b7d",
    "Jupyter Notebook": "#da5b0b",
    "Shell": "#89e051",
    "Other": "#888888",
}

# =========================
# TEMAS (COMPLETOS)
# =========================

THEMES = {
    "cobalt": {
        "background": "#0047AB",
        "title": "#FFC600",
        "text": "#FFFFFF",
        "icon": "#FFC600",
        "border": "#333",
        "rank_circle_bg": "#333",
        "rank_circle_fill": "#FFC600",
    },
    "dark": {
        "background": "#151515",
        "title": "#ffffff",
        "text": "#9f9f9f",
        "icon": "#ffffff",
        "border": "#e4e2e2",
        "rank_circle_bg": "#333",
        "rank_circle_fill": "#ffffff",
    },
    "dracula": {
        "background": "#282a36",
        "title": "#f8f8f2",
        "text": "#f8f8f2",
        "icon": "#f8f8f2",
        "border": "#44475a",
        "rank_circle_bg": "#44475a",
        "rank_circle_fill": "#ff79c6",
    },
    "gruvbox": {
        "background": "#282828",
        "title": "#fabd2f",
        "text": "#ebdbb2",
        "icon": "#fabd2f",
        "border": "#504945",
        "rank_circle_bg": "#504945",
        "rank_circle_fill": "#fabd2f",
    },
    "merko": {
        "background": "#0a0f0d",
        "title": "#ef553b",
        "text": "#a2a2a2",
        "icon": "#ef553b",
        "border": "#ef553b",
        "rank_circle_bg": "#2d2d2d",
        "rank_circle_fill": "#ef553b",
    },
    "onedark": {
        "background": "#282c34",
        "title": "#61afef",
        "text": "#abb2bf",
        "icon": "#61afef",
        "border": "#3e4451",
        "rank_circle_bg": "#3e4451",
        "rank_circle_fill": "#61afef",
    },
    "radical": {
        "background": "#141321",
        "title": "#fe428e",
        "text": "#a9fef7",
        "icon": "#fe428e",
        "border": "#fe428e",
        "rank_circle_bg": "#54253a",
        "rank_circle_fill": "#fe428e",
    },
    "tokyonight": {
        "background": "#1a1b27",
        "title": "#70a5fd",
        "text": "#a9b1d6",
        "icon": "#70a5fd",
        "border": "#414868",
        "rank_circle_bg": "#414868",
        "rank_circle_fill": "#70a5fd",
    },
}

THEME = THEMES.get(THEME_NAME, THEMES["merko"])

# =========================
# API SAFE CALL
# =========================

def safe_get(url, params=None):
    for _ in range(3):
        r = SESSION.get(url, params=params)
        if r.status_code == 429:
            time.sleep(2)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("GitHub API rate limit excedido.")

# =========================
# FETCH DATA
# =========================

def fetch_repos(username):
    repos = []
    page = 1
    while True:
        data = safe_get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_languages(username):
    repos = fetch_repos(username)
    totals = defaultdict(int)

    for repo in repos:
        if repo.get("fork"):
            continue
        langs = safe_get(repo["languages_url"])
        for lang, value in langs.items():
            totals[lang] += value

    total = sum(totals.values()) or 1
    langs_percent = [
        (lang, (value / total) * 100)
        for lang, value in totals.items()
    ]

    return sorted(langs_percent, key=lambda x: x[1], reverse=True)[:6]

# =========================
# SVG COMPONENTES
# =========================

def avatar_svg(cx, cy, r):
    return f"""
    <circle cx="{cx}" cy="{cy}" r="{r+8}" fill="{THEME['rank_circle_bg']}"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{THEME['background']}"
            stroke="{THEME['rank_circle_fill']}" stroke-width="2"/>
    <text x="{cx}" y="{cy+12}" text-anchor="middle"
          font-size="36" fill="{THEME['icon']}"
          font-family="monospace" font-weight="bold">
      &lt;/&gt;
    </text>
    """

def progress_bar(x, y, width, percent, color):
    fill = width * (percent / 100)
    return f"""
    <rect x="{x}" y="{y}" width="{width}" height="10" rx="5"
          fill="{THEME['rank_circle_bg']}"/>
    <rect x="{x}" y="{y}" width="{fill}" height="10" rx="5"
          fill="{color}">
      <animate attributeName="width" from="0" to="{fill}"
               dur="1s" fill="freeze"/>
    </rect>
    """

# =========================
# SVG FINAL
# =========================

def create_top_languages_svg(username, langs):
    width, height = 720, 380
    y = 165

    rows = ""
    for i, (lang, percent) in enumerate(langs, 1):
        color = LANG_COLORS.get(lang, LANG_COLORS["Other"])
        rows += f"""
        <text x="90" y="{y}" fill="{THEME['text']}" font-size="14">
          {i}. {lang}
        </text>
        {progress_bar(220, y-10, 400, percent, color)}
        <text x="640" y="{y}" fill="{THEME['text']}" font-size="12">
          {percent:.1f}%
        </text>
        """
        y += 30

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    svg = f"""
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
         xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" rx="20"
            fill="{THEME['background']}" stroke="{THEME['border']}"/>

      {avatar_svg(80, 80, 38)}

      <text x="140" y="55" fill="{THEME['title']}"
            font-size="22" font-weight="bold">
        Domisnnet · Developer Dashboard
      </text>
      <text x="140" y="78" fill="{THEME['text']}" font-size="13">
        Da faísca da ideia à constelação do código.
      </text>
      <text x="140" y="96" fill="{THEME['text']}" font-size="12" opacity="0.85">
        Construindo um universo de possibilidades.
      </text>

      <text x="90" y="135" fill="{THEME['icon']}"
            font-size="16" font-weight="bold">
        Top Languages · GitHub Activity
      </text>

      {rows}

      <text x="90" y="{height-22}" fill="{THEME['text']}"
            font-size="11" opacity="0.6">
        Updated: {updated}
      </text>
    </svg>
    """

    with open("top-langs.svg", "w", encoding="utf-8") as f:
        f.write(svg)

# =========================
# MAIN
# =========================

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    langs = fetch_languages(username)
    create_top_languages_svg(username, langs)
    print("SVG gerado com sucesso.")

if __name__ == "__main__":
    main()