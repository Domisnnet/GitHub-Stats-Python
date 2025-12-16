import os
import sys
import math
import logging
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}

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
    "Other": "#ededed",
    "PHP": "#4F5D95",
    "Python": "#3572A5",
    "Ruby": "#701516",
    "Shell": "#89e051",
    "TypeScript": "#2b7489",
}

THEMES = {
    "cobalt": {
        "background": "#0047AB",
        "title": "#FFC600",
        "text": "#FFFFFF",
        "icon": "#FFC600",
        "border": "#333",
        "rank_circle_bg": "#333",
        "rank_circle_fill": "#FFC600",
        "lang_colors": LANG_COLORS,
    },
    "dark": {
        "background": "#151515",
        "title": "#ffffff",
        "text": "#9f9f9f",
        "icon": "#ffffff",
        "border": "#e4e2e2",
        "rank_circle_bg": "#333",
        "rank_circle_fill": "#ffffff",
        "lang_colors": LANG_COLORS,
    },
    "dracula": {
        "background": "#282a36",
        "title": "#f8f8f2",
        "text": "#f8f8f2",
        "icon": "#f8f8f2",
        "border": "#44475a",
        "rank_circle_bg": "#44475a",
        "rank_circle_fill": "#ff79c6",
        "lang_colors": LANG_COLORS,
    },
    "gruvbox": {
        "background": "#282828",
        "title": "#fabd2f",
        "text": "#ebdbb2",
        "icon": "#fabd2f",
        "border": "#504945",
        "rank_circle_bg": "#504945",
        "rank_circle_fill": "#fabd2f",
        "lang_colors": LANG_COLORS,
    },
    "merko": {
        "background": "#0a0f0d",
        "title": "#ef553b",
        "text": "#a2a2a2",
        "icon": "#ef553b",
        "border": "#ef553b",
        "rank_circle_bg": "#2d2d2d",
        "rank_circle_fill": "#ef553b",
        "lang_colors": LANG_COLORS,
    },
    "onedark": {
        "background": "#282c34",
        "title": "#61afef",
        "text": "#abb2bf",
        "icon": "#61afef",
        "border": "#3e4451",
        "rank_circle_bg": "#3e4451",
        "rank_circle_fill": "#61afef",
        "lang_colors": LANG_COLORS,
    },
    "radical": {
        "background": "#141321",
        "title": "#fe428e",
        "text": "#a9fef7",
        "icon": "#fe428e",
        "border": "#fe428e",
        "rank_circle_bg": "#54253a",
        "rank_circle_fill": "#fe428e",
        "lang_colors": LANG_COLORS,
    },
    "tokyonight": {
        "background": "#1a1b27",
        "title": "#70a5fd",
        "text": "#a9b1d6",
        "icon": "#70a5fd",
        "border": "#414868",
        "rank_circle_bg": "#414868",
        "rank_circle_fill": "#70a5fd",
        "lang_colors": LANG_COLORS,
    },
}

def fetch_top_languages(username: str) -> Counter:
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"
    r = requests.get(repos_url, headers=HEADERS, timeout=10)
    r.raise_for_status()

    counter = Counter()
    for repo in r.json():
        url = repo.get("languages_url")
        if not url:
            continue
        lr = requests.get(url, headers=HEADERS, timeout=10)
        if lr.ok:
            for lang, size in lr.json().items():
                counter[lang] += size
    return counter

def create_top_langs_svg(langs: Counter, theme_name: str) -> str:
    theme = THEMES.get(theme_name, THEMES["merko"])
    clip_id = "rounded-corners-langs"

    if not langs:
        return f"""
<svg width="600" height="230" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{theme['background']}" rx="5"/>
  <text x="50%" y="50%" fill="#ff4a4a" text-anchor="middle"
        font-family="Segoe UI, Ubuntu, Sans-Serif">Failed to fetch language data</text>
</svg>
""".strip()

    total = sum(langs.values())
    top = langs.most_common(6)

    BAR_W = 550
    BAR_H = 16
    BAR_R = 8
    x = 0
    bars = []

    for lang, size in top:
        w = (size / total) * BAR_W
        color = theme["lang_colors"].get(lang, "#ededed")
        bars.append(f'<rect x="{x}" y="0" width="{w}" height="{BAR_H}" fill="{color}"/>')
        x += w

    legend = ""
    for i, (lang, size) in enumerate(top):
        pct = size / total * 100
        lx = 20 if i < 3 else 300
        ly = 110 + (i % 3) * 25
        color = theme["lang_colors"].get(lang, "#ededed")
        legend += f"""
<g transform="translate({lx},{ly})">
  <rect width="10" height="10" rx="2" fill="{color}"/>
  <text x="15" y="10" font-size="12" fill="{theme['text']}"
        font-family="Segoe UI, Ubuntu, Sans-Serif">{lang} ({pct:.1f}%)</text>
</g>
"""

    return f"""
<svg width="600" height="230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="{clip_id}">
      <rect width="{BAR_W}" height="{BAR_H}" rx="{BAR_R}"/>
    </clipPath>
  </defs>

  <rect x="1" y="1" width="598" height="228" rx="5"
        fill="{theme['background']}" stroke="{theme['border']}" stroke-width="2"/>

  <text x="20" y="30" font-size="18" font-weight="bold"
        fill="{theme['title']}" font-family="Segoe UI, Ubuntu, Sans-Serif">
    Top Languages
  </text>

  <g transform="translate(25,65)">
    <rect width="{BAR_W}" height="{BAR_H}" fill="{theme['rank_circle_bg']}" rx="{BAR_R}"/>
    <g clip-path="url(#{clip_id})">
      {''.join(bars)}
    </g>
  </g>

  {legend}
</svg>
""".strip()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    username = sys.argv[1]
    langs = fetch_top_languages(username)
    svg = create_top_langs_svg(langs, THEME_NAME)

    with open("top-langs.svg", "w", encoding="utf-8") as f:
        f.write(svg)