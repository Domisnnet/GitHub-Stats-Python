import os
import sys
import math
import time
import requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

USERNAME = sys.argv[1] if len(sys.argv) > 1 else None
TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})
}

# ================= LANG COLORS =================

LANG_COLORS = {
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "HTML": "#e34c26",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "Shell": "#89e051",
    "TypeScript": "#2b7489",
    "Other": "#999999",
}

# ================= THEMES =================

THEMES = {
    "cobalt": {
        "bg": "#0047AB",
        "panel": "#003a8c",
        "title": "#FFC600",
        "text": "#ffffff",
        "muted": "#d6d6d6",
        "border": "#002f6c",
        "accent": "#FFC600",
        "bar_bg": "#003060",
    },
    "dark": {
        "bg": "#151515",
        "panel": "#1f1f1f",
        "title": "#ffffff",
        "text": "#cfcfcf",
        "muted": "#9f9f9f",
        "border": "#e4e2e2",
        "accent": "#ffffff",
        "bar_bg": "#2a2a2a",
    },
    "dracula": {
        "bg": "#282a36",
        "panel": "#303241",
        "title": "#ff79c6",
        "text": "#f8f8f2",
        "muted": "#bfbfbf",
        "border": "#44475a",
        "accent": "#ff79c6",
        "bar_bg": "#3b3d4d",
    },
    "gruvbox": {
        "bg": "#282828",
        "panel": "#32302f",
        "title": "#fabd2f",
        "text": "#ebdbb2",
        "muted": "#bdae93",
        "border": "#504945",
        "accent": "#fabd2f",
        "bar_bg": "#3c3836",
    },
    "merko": {
        "bg": "#0a0f0d",
        "panel": "#111816",
        "title": "#ef553b",
        "text": "#c9c9c9",
        "muted": "#8b8b8b",
        "border": "#ef553b",
        "accent": "#ef553b",
        "bar_bg": "#1f1f1f",
    },
    "onedark": {
        "bg": "#282c34",
        "panel": "#2f343f",
        "title": "#61afef",
        "text": "#abb2bf",
        "muted": "#7f848e",
        "border": "#3e4451",
        "accent": "#61afef",
        "bar_bg": "#3b4048",
    },
    "radical": {
        "bg": "#141321",
        "panel": "#1c1b2f",
        "title": "#fe428e",
        "text": "#e4e4e4",
        "muted": "#a9a9a9",
        "border": "#fe428e",
        "accent": "#fe428e",
        "bar_bg": "#2a2845",
    },
    "tokyonight": {
        "bg": "#1a1b27",
        "panel": "#20212e",
        "title": "#70a5fd",
        "text": "#c0caf5",
        "muted": "#9aa5ce",
        "border": "#414868",
        "accent": "#70a5fd",
        "bar_bg": "#2a2c3f",
    },
}

THEME = THEMES.get(THEME_NAME, THEMES["merko"])

# ================= HELPERS =================

def safe_get(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        time.sleep(3)
        return safe_get(url)
    r.raise_for_status()
    return r.json()

# ================= FETCH =================

def fetch_user():
    return safe_get(f"https://api.github.com/users/{USERNAME}")

def fetch_repos():
    return safe_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")

def fetch_languages(repos):
    counter = Counter()
    for repo in repos:
        try:
            langs = safe_get(repo["languages_url"])
            for lang, size in langs.items():
                counter[lang] += size
        except Exception:
            continue
    return counter

# ================= SVG =================

def build_svg(user, repos, langs):
    width, height = 1000, 320

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="100%" height="100%" rx="22"
  fill="{THEME['bg']}" stroke="{THEME['border']}" stroke-width="3" />

<text x="140" y="60" fill="{THEME['title']}" font-size="26" font-weight="bold">
  {user['name'] or user['login']} · Developer Dashboard
</text>

<text x="140" y="90" fill="{THEME['muted']}" font-size="14">
  Da faísca da ideia à Constelação do código. Construindo um Universo de possibilidades!!
</text>

<text x="140" y="130" fill="{THEME['text']}" font-size="14">
  ⭐ {sum(r['stargazers_count'] for r in repos)} stars · 📦 {len(repos)} repositórios
</text>

</svg>'''

# ================= MAIN =================

def main():
    if not USERNAME:
        sys.exit(1)

    user = fetch_user()
    repos = fetch_repos()
    langs = fetch_languages(repos)

    svg = build_svg(user, repos, langs)

    with open("dashboard.svg", "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    main()