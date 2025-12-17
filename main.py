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
    "C": "#555555",
    "C++": "#f34b7d",
    "CSS": "#563d7c",
    "Cython": "#fedf5b",
    "Go": "#00ADD8",
    "HTML": "#e34c26",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B",
    "PHP": "#4F5D95",
    "Python": "#3572A5",
    "Ruby": "#701516",
    "Shell": "#89e051",
    "TypeScript": "#2b7489",
    "Other": "#ededed",
}

# ================= THEMES =================

THEMES = {
    "cobalt": {
        "bg": "#0047AB", "title": "#FFC600", "text": "#FFFFFF",
        "border": "#333", "accent": "#FFC600"
    },
    "dark": {
        "bg": "#151515", "title": "#ffffff", "text": "#9f9f9f",
        "border": "#e4e2e2", "accent": "#ffffff"
    },
    "dracula": {
        "bg": "#282a36", "title": "#f8f8f2", "text": "#f8f8f2",
        "border": "#44475a", "accent": "#ff79c6"
    },
    "gruvbox": {
        "bg": "#282828", "title": "#fabd2f", "text": "#ebdbb2",
        "border": "#504945", "accent": "#fabd2f"
    },
    "merko": {
        "bg": "#0a0f0d", "title": "#ef553b", "text": "#a2a2a2",
        "border": "#ef553b", "accent": "#ef553b"
    },
    "onedark": {
        "bg": "#282c34", "title": "#61afef", "text": "#abb2bf",
        "border": "#3e4451", "accent": "#61afef"
    },
    "radical": {
        "bg": "#141321", "title": "#fe428e", "text": "#a9fef7",
        "border": "#fe428e", "accent": "#fe428e"
    },
    "tokyonight": {
        "bg": "#1a1b27", "title": "#70a5fd", "text": "#a9b1d6",
        "border": "#414868", "accent": "#70a5fd"
    },
}

THEME = THEMES.get(THEME_NAME, THEMES["merko"])

# ================= HELPERS =================

def safe_get(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        time.sleep(2)
        return safe_get(url)
    r.raise_for_status()
    return r.json()

def k(n):
    return f"{n//1000}k+" if n >= 1000 else str(n)

# ================= FETCH =================

def fetch_user():
    return safe_get(f"https://api.github.com/users/{USERNAME}")

def fetch_repos():
    return safe_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")

def fetch_languages(repos):
    counter = Counter()
    for r in repos:
        try:
            data = safe_get(r["languages_url"])
            for lang, val in data.items():
                counter[lang] += val
        except:
            continue
    return counter

# ================= SVG BLOCKS =================

def render_top_languages(counter, x=260, y=260):
    total = sum(counter.values())
    top = counter.most_common(5)

    BAR_MAX = 360
    BAR_HEIGHT = 10
    GAP = 26

    svg = ""
    y_pos = y

    for lang, val in top:
        pct = (val / total) * 100
        width = BAR_MAX * (pct / 100)
        color = LANG_COLORS.get(lang, LANG_COLORS["Other"])

        svg += f'''
<g>
  <text x="{x}" y="{y_pos}" fill="{THEME['text']}" font-size="12">
    {lang}
  </text>

  <rect x="{x+90}" y="{y_pos-9}"
    width="{BAR_MAX}" height="{BAR_HEIGHT}"
    rx="5" fill="#1e1e1e"/>

  <rect x="{x+90}" y="{y_pos-9}"
    width="{width}" height="{BAR_HEIGHT}"
    rx="5" fill="{color}"/>

  <text x="{x+90+BAR_MAX+10}" y="{y_pos}"
    fill="{THEME['text']}" font-size="12">
    {pct:.1f}%
  </text>
</g>
'''
        y_pos += GAP

    return svg

# ================= MAIN SVG =================

def build_svg(user, repos, langs):
    stars = sum(r["stargazers_count"] for r in repos)

    return f'''
<svg width="900" height="360" xmlns="http://www.w3.org/2000/svg">

<rect width="100%" height="100%" rx="28"
 fill="{THEME['bg']}"
 stroke="{THEME['border']}"
 stroke-width="4"/>

<!-- Ícone -->
<circle cx="90" cy="90" r="32"
 fill="none" stroke="{THEME['accent']}" stroke-width="3"/>
<text x="90" y="98" text-anchor="middle"
 fill="{THEME['accent']}" font-size="18">&lt;/&gt;</text>

<!-- Título -->
<text x="140" y="70" fill="{THEME['title']}"
 font-size="22" font-weight="bold">
 Domisnnet · Developer Dashboard
</text>

<text x="140" y="96" fill="{THEME['text']}" font-size="13">
 Da faísca da ideia à Constelação do código.
</text>

<text x="140" y="118" fill="{THEME['text']}" font-size="13">
 Construindo um Universo de possibilidades!!
</text>

<!-- Stats -->
<text x="140" y="150" fill="{THEME['text']}" font-size="13">
 📦 Repositórios: {len(repos)}   ⭐ Stars: {stars}
</text>

<!-- Qualificação -->
<circle cx="820" cy="90" r="26"
 fill="none" stroke="{THEME['accent']}" stroke-width="4"/>
<text x="820" y="98" text-anchor="middle"
 fill="{THEME['accent']}" font-size="18" font-weight="bold">
 A
</text>

<!-- Linguagens -->
<text x="260" y="230"
 fill="{THEME['accent']}" font-size="16" font-weight="bold">
 Top Languages
</text>

{render_top_languages(langs)}

</svg>
'''

# ================= ENTRY =================

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