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

# ================= LANG COLORS (alfabético) =================

LANG_COLORS = {
    "CSS": "#563d7c",
    "Dockerfile": "#384d54",
    "Go": "#00ADD8",
    "HTML": "#e34c26",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "Markdown": "#083fa1",
    "Python": "#3572A5",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
    "TypeScript": "#2b7489",
    "Vue": "#41b883",
    "Other": "#999999",
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

def safe_get(url, retries=3):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429 and retries > 0:
        time.sleep(3)
        return safe_get(url, retries - 1)
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
        except Exception:
            continue
    return counter

# ================= SVG BUILD =================

def build_activity_ring(langs, cx, cy, radius):
    total = sum(langs.values())
    if total == 0:
        return ""

    circumference = 2 * math.pi * radius
    offset = 0
    svg = ""

    for lang, val in langs.most_common(6):
        frac = val / total
        length = frac * circumference
        color = LANG_COLORS.get(lang, LANG_COLORS["Other"])

        svg += f'''
<circle cx="{cx}" cy="{cy}" r="{radius}"
  fill="none"
  stroke="{color}"
  stroke-width="22"
  stroke-dasharray="{length} {circumference-length}"
  stroke-dashoffset="{-offset}"
  stroke-linecap="round"
  transform="rotate(-90 {cx} {cy})"/>
'''
        offset += length

    return svg

def build_avatar(user, cx, cy):
    avatar_url = user.get("avatar_url", "") + "&s=128"

    return f'''
<defs>
  <radialGradient id="avatarGlow" r="60%">
    <stop offset="0%" stop-color="{THEME['accent']}" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="{THEME['accent']}" stop-opacity="0"/>
  </radialGradient>

  <clipPath id="avatarClip">
    <circle cx="{cx}" cy="{cy}" r="46"/>
  </clipPath>
</defs>

<circle cx="{cx}" cy="{cy}" r="62" fill="url(#avatarGlow)"/>
<circle cx="{cx}" cy="{cy}" r="52"
  fill="none"
  stroke="{THEME['accent']}"
  stroke-width="3"/>

<image href="{avatar_url}"
  x="{cx-46}" y="{cy-46}"
  width="92" height="92"
  clip-path="url(#avatarClip)"
  preserveAspectRatio="xMidYMid slice"/>
'''

def build_svg(user, repos, langs):
    stars = sum(r["stargazers_count"] for r in repos)
    cx, cy = 450, 300

    return f'''
<svg width="900" height="600" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" rx="28"
  fill="{THEME['bg']}"
  stroke="{THEME['border']}"
  stroke-width="4"/>

<text x="450" y="60" text-anchor="middle"
  fill="{THEME['title']}" font-size="24" font-weight="bold">
{user.get("name") or user.get("login")}
</text>

<text x="450" y="88" text-anchor="middle"
  fill="{THEME['text']}" font-size="14">
Da faísca da ideia à Constelação do código.
</text>

<text x="450" y="108" text-anchor="middle"
  fill="{THEME['text']}" font-size="13">
Construindo um Universo de possibilidades!!
</text>

{build_activity_ring(langs, cx, cy, 150)}
{build_avatar(user, cx, cy)}

<text x="450" y="520" text-anchor="middle"
  fill="{THEME['text']}" font-size="14">
⭐ {k(stars)} stars · 📦 {len(repos)} repositórios
</text>

</svg>
'''

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