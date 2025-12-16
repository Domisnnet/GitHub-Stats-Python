import os
import sys
import math
import time
import logging
import requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})
}

LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "Shell": "#89e051",
    "Other": "#ededed"
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

def safe_get(url, sleep=0.4):
    time.sleep(sleep)
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 429:
        logging.warning("Rate limit atingido. Abortando execução.")
        sys.exit(0)
    r.raise_for_status()
    return r.json(), r.headers

def fetch_repos(username):
    data, _ = safe_get(f"https://api.github.com/users/{username}/repos?per_page=100&type=owner")
    return data

def fetch_languages(username):
    repos = fetch_repos(username)
    counter = Counter()

    for repo in repos:
        if not repo.get("languages_url"):
            continue
        try:
            langs, _ = safe_get(repo["languages_url"], sleep=0.2)
            for lang, size in langs.items():
                counter[lang] += size
        except Exception:
            continue

    return counter

def create_stats_svg(username, theme_name):
    theme = THEMES.get(theme_name, THEMES["merko"])

    return f"""
<svg width="600" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="22"
        fill="{theme['background']}"
        stroke="{theme['border']}"
        stroke-width="2.5"/>

  <text x="30" y="45" font-size="22" fill="{theme['title']}"
        font-family="Segoe UI, Ubuntu, Sans-Serif"
        font-weight="bold">
    Domisnnet · Developer Dashboard
  </text>

  <text x="30" y="75" font-size="13" fill="{theme['text']}"
        opacity="0.85"
        font-family="Segoe UI, Ubuntu, Sans-Serif">
    Da faísca da idéia à Constelação do código.
  </text>

  <text x="30" y="95" font-size="13" fill="{theme['text']}"
        opacity="0.65"
        font-family="Segoe UI, Ubuntu, Sans-Serif">
    Construindo um Universo de possibilidades!!
  </text>

</svg>
""".strip()

def create_langs_svg(langs, theme_name):
    theme = THEMES.get(theme_name, THEMES["merko"])
    total = sum(langs.values())
    top = langs.most_common(6)

    x = 25
    bars = ""
    for lang, size in top:
        w = int((size / total) * 500)
        color = theme["lang_colors"].get(lang, "#ccc")
        bars += f'<rect x="{x}" y="90" width="{w}" height="14" fill="{color}" rx="7"/>\n'
        x += w

    return f"""
<svg width="600" height="180" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="22"
        fill="{theme['background']}"
        stroke="{theme['border']}"
        stroke-width="2.5"/>

  <text x="30" y="45" font-size="18" fill="{theme['title']}"
        font-family="Segoe UI, Ubuntu, Sans-Serif"
        font-weight="bold">
    Top Languages
  </text>

  {bars}
</svg>
""".strip()

def main():
    username = sys.argv[1]
    langs = fetch_languages(username)

    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(create_stats_svg(username, THEME_NAME))

    with open("top-langs.svg", "w", encoding="utf-8") as f:
        f.write(create_langs_svg(langs, THEME_NAME))

if __name__ == "__main__":
    main()