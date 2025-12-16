import os
import sys
import math
import logging
import requests
from collections import Counter
from dotenv import load_dotenv
from datetime import datetime

# -------------------------------------------------
# SETUP
# -------------------------------------------------
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}

# -------------------------------------------------
# LANGUAGE COLORS
# -------------------------------------------------
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "C": "#555555",
    "C++": "#f34b7d",
    "Go": "#00ADD8",
    "Shell": "#89e051",
    "Jupyter Notebook": "#DA5B0B",
    "Cython": "#fedf5b",
}

# -------------------------------------------------
# THEMES (EXATAMENTE OS QUE VOCÊ PEDIU)
# -------------------------------------------------
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

# -------------------------------------------------
# API HELPERS
# -------------------------------------------------
def fetch_repos(username: str) -> list:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"
    r = requests.get(url, headers=HEADERS, timeout=15)

    if r.status_code == 429:
        logging.warning("Rate limit atingido ao buscar repositórios.")
        return []

    r.raise_for_status()
    return r.json()


def fetch_languages(repos: list) -> Counter:
    counter = Counter()

    for repo in repos:
        url = repo.get("languages_url")
        if not url:
            continue

        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 429:
            continue
        if not r.ok:
            continue

        for lang, size in r.json().items():
            counter[lang] += size

    return counter


def fetch_basic_stats(repos: list) -> dict:
    stars = sum(r.get("stargazers_count", 0) for r in repos)

    return {
        "stars": stars,
        "repos": len(repos),
    }


# -------------------------------------------------
# SVG — TOP LANGUAGES WOW
# -------------------------------------------------
def create_top_languages_svg(langs: Counter, theme_name: str) -> str:
    theme = THEMES.get(theme_name, THEMES["merko"])

    if not langs:
        return "<svg></svg>"

    total = sum(langs.values())
    top = langs.most_common(5)
    dominant, dominant_size = top[0]
    dominant_pct = dominant_size / total * 100

    bars = ""
    y = 140
    max_width = 360

    for i, (lang, size) in enumerate(top):
        pct = size / total * 100
        width = (pct / 100) * max_width
        color = theme["lang_colors"].get(lang, "#888")

        bars += f"""
        <text x="40" y="{y}" fill="{theme['text']}" font-size="13">{i+1}</text>
        <text x="65" y="{y}" fill="{theme['text']}" font-size="13">{lang}</text>
        <rect x="200" y="{y-10}" rx="6" ry="6" width="{width}" height="10" fill="{color}"/>
        <text x="570" y="{y}" fill="{theme['text']}" font-size="12" text-anchor="end">{pct:.1f}%</text>
        """
        y += 28

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    return f"""
<svg width="600" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="598" height="298" x="1" y="1" rx="14" ry="14"
        fill="{theme['background']}" stroke="{theme['border']}" stroke-width="2"/>

  <text x="40" y="40" fill="{theme['title']}" font-size="20" font-weight="600">
    Top Languages · GitHub Activity
  </text>

  <text x="40" y="70" fill="#00f5a0" font-size="14">
    Dominant Stack: {dominant} ({dominant_pct:.1f}%)
  </text>

  <rect x="40" y="95" rx="10" ry="10" width="520" height="14" fill="#1f2a2a"/>
  <rect x="40" y="95" rx="10" ry="10" width="{520 * dominant_pct / 100}"
        height="14" fill="#00f5a0"/>

  {bars}

  <text x="40" y="275" fill="{theme['text']}" font-size="11">
    Languages: {len(langs)} · Updated: {updated}
  </text>
</svg>
""".strip()


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    username = sys.argv[1]
    theme = THEME_NAME

    repos = fetch_repos(username)

    stats = fetch_basic_stats(repos)
    langs = fetch_languages(repos)

    langs_svg = create_top_languages_svg(langs, theme)

    with open("top-langs.svg", "w", encoding="utf-8") as f:
        f.write(langs_svg)

    logging.info("SVG gerado com sucesso.")


if __name__ == "__main__":
    main()