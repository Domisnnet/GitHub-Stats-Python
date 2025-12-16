import os
import sys
import time
import math
import requests
from datetime import datetime
from collections import defaultdict

# ======================================================
# CONFIG
# ======================================================

GITHUB_API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}" if TOKEN else None,
}

SESSION = requests.Session()
SESSION.headers.update({k: v for k, v in HEADERS.items() if v})

# ======================================================
# LANG COLORS
# ======================================================

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

# ======================================================
# THEMES
# ======================================================

THEMES = {
    "cobalt": {
        "background": "#0047AB", "title": "#FFC600", "text": "#FFFFFF",
        "icon": "#FFC600", "border": "#333",
        "rank_circle_bg": "#333", "rank_circle_fill": "#FFC600",
    },
    "dark": {
        "background": "#151515", "title": "#ffffff", "text": "#9f9f9f",
        "icon": "#ffffff", "border": "#e4e2e2",
        "rank_circle_bg": "#333", "rank_circle_fill": "#ffffff",
    },
    "dracula": {
        "background": "#282a36", "title": "#f8f8f2", "text": "#f8f8f2",
        "icon": "#f8f8f2", "border": "#44475a",
        "rank_circle_bg": "#44475a", "rank_circle_fill": "#ff79c6",
    },
    "gruvbox": {
        "background": "#282828", "title": "#fabd2f", "text": "#ebdbb2",
        "icon": "#fabd2f", "border": "#504945",
        "rank_circle_bg": "#504945", "rank_circle_fill": "#fabd2f",
    },
    "merko": {
        "background": "#0a0f0d", "title": "#ef553b", "text": "#a2a2a2",
        "icon": "#ef553b", "border": "#ef553b",
        "rank_circle_bg": "#2d2d2d", "rank_circle_fill": "#ef553b",
    },
    "onedark": {
        "background": "#282c34", "title": "#61afef", "text": "#abb2bf",
        "icon": "#61afef", "border": "#3e4451",
        "rank_circle_bg": "#3e4451", "rank_circle_fill": "#61afef",
    },
    "radical": {
        "background": "#141321", "title": "#fe428e", "text": "#a9fef7",
        "icon": "#fe428e", "border": "#fe428e",
        "rank_circle_bg": "#54253a", "rank_circle_fill": "#fe428e",
    },
    "tokyonight": {
        "background": "#1a1b27", "title": "#70a5fd", "text": "#a9b1d6",
        "icon": "#70a5fd", "border": "#414868",
        "rank_circle_bg": "#414868", "rank_circle_fill": "#70a5fd",
    },
}

THEME = THEMES.get(THEME_NAME, THEMES["cobalt"])

# ======================================================
# API SAFE
# ======================================================

def safe_get(url, params=None):
    for _ in range(3):
        r = SESSION.get(url, params=params)
        if r.status_code == 429:
            time.sleep(2)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Rate limit excedido.")

# ======================================================
# FETCH
# ======================================================

def fetch_repos(username):
    repos, page = [], 1
    while True:
        data = safe_get(
            f"{GITHUB_API}/users/{username}/repos",
            {"per_page": 100, "page": page, "type": "owner"},
        )
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_stats(username):
    repos = fetch_repos(username)

    stats = {
        "repos": len(repos),
        "stars": sum(r["stargazers_count"] for r in repos),
        "forks": sum(r["forks_count"] for r in repos),
        "commits": len(repos) * 30,  # aproximação segura
    }
    return stats

def fetch_languages(username):
    repos = fetch_repos(username)
    totals = defaultdict(int)

    for repo in repos:
        if repo.get("fork"):
            continue
        langs = safe_get(repo["languages_url"])
        for lang, val in langs.items():
            totals[lang] += val

    total = sum(totals.values()) or 1
    data = [(l, v / total * 100) for l, v in totals.items()]
    return sorted(data, key=lambda x: x[1], reverse=True)[:5]

# ======================================================
# SCORE
# ======================================================

def calculate_score(stats):
    raw = (
        stats["repos"] * 2
        + stats["stars"] * 5
        + stats["forks"] * 3
        + stats["commits"] * 0.1
    )
    return min(100, int(raw / 10))

# ======================================================
# SVG COMPONENTS
# ======================================================

def avatar(cx, cy):
    return f"""
    <circle cx="{cx}" cy="{cy}" r="38" fill="{THEME['rank_circle_bg']}"/>
    <circle cx="{cx}" cy="{cy}" r="34"
        fill="{THEME['background']}"
        stroke="{THEME['rank_circle_fill']}" stroke-width="2"/>
    <text x="{cx}" y="{cy+12}" text-anchor="middle"
        font-size="34" font-family="monospace"
        fill="{THEME['icon']}">&lt;/&gt;</text>
    """

def rank_circle(cx, cy, percent):
    r = 42
    c = 2 * math.pi * r
    dash = c * percent / 100
    return f"""
    <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="{THEME['rank_circle_bg']}"
        stroke-width="8"/>
    <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="{THEME['rank_circle_fill']}"
        stroke-width="8"
        stroke-dasharray="{dash} {c}">
        <animate attributeName="stroke-dasharray"
            from="0 {c}" to="{dash} {c}"
            dur="1.2s" fill="freeze"/>
    </circle>
    <text x="{cx}" y="{cy+6}" text-anchor="middle"
        font-size="18" fill="{THEME['title']}">{percent}%</text>
    """

# ======================================================
# SVG DASHBOARD
# ======================================================

def create_dashboard(username, stats, score, langs):
    w, h = 820, 420
    y = 250
    bars = ""

    for lang, pct in langs:
        color = LANG_COLORS.get(lang, LANG_COLORS["Other"])
        bars += f"""
        <text x="120" y="{y}" fill="{THEME['text']}" font-size="13">{lang}</text>
        <rect x="220" y="{y-10}" width="400" height="10" rx="5"
            fill="{THEME['rank_circle_bg']}"/>
        <rect x="220" y="{y-10}" width="{4*pct}" height="10" rx="5"
            fill="{color}"/>
        """
        y += 26

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    svg = f"""
    <svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"
        xmlns="http://www.w3.org/2000/svg">

    <rect width="100%" height="100%" rx="22"
        fill="{THEME['background']}" stroke="{THEME['border']}"/>

    {avatar(90, 90)}
    {rank_circle(90, 200, score)}

    <text x="160" y="55" fill="{THEME['title']}"
        font-size="24" font-weight="bold">
        Domisnnet · Developer Dashboard
    </text>
    <text x="160" y="80" fill="{THEME['text']}" font-size="14">
        Da faísca da ideia à constelação do código.
    </text>
    <text x="160" y="100" fill="{THEME['text']}" font-size="13" opacity="0.85">
        Construindo um Universo de possibilidades!!
    </text>

    <text x="160" y="140" fill="{THEME['icon']}" font-size="14">
        Repos: {stats['repos']}  •  Stars: {stats['stars']}
        • Forks: {stats['forks']}
    </text>

    {bars}

    <text x="40" y="{h-18}" fill="{THEME['text']}"
        font-size="11" opacity="0.6">
        Updated: {updated}
    </text>

    </svg>
    """

    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)

# ======================================================
# MAIN
# ======================================================

def main():
    username = sys.argv[1]
    stats = fetch_stats(username)
    langs = fetch_languages(username)
    score = calculate_score(stats)

    create_dashboard(username, stats, score, langs)
    print("Dashboard Fase 3 gerado com sucesso.")

if __name__ == "__main__":
    main()