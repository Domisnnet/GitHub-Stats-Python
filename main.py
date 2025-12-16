import os
import math
import requests
from collections import Counter
from datetime import datetime

# ---------------- CONFIG ----------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}

# ---------------- LANG COLORS ----------------
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "Shell": "#89e051",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Other": "#ededed",
}

# ---------------- RAW THEMES ----------------
RAW_THEMES = {
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

# ---------------- THEME NORMALIZER ----------------
def normalize_theme(theme_name: str) -> dict:
    raw = RAW_THEMES.get(theme_name, RAW_THEMES["merko"])
    return {
        "bg": raw["background"],
        "text": raw["text"],
        "muted": raw["text"],
        "accent": raw["rank_circle_fill"],
        "border": raw["border"],
        "track": raw["rank_circle_bg"],
        "title": raw["title"],
        "icon": raw["icon"],
        "lang_colors": raw["lang_colors"],
    }

# ---------------- HELPERS ----------------
def k(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)

# ---------------- GITHUB API ----------------
def fetch_user(username: str) -> dict:
    r = requests.get(f"https://api.github.com/users/{username}", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def fetch_repos(username: str) -> list:
    r = requests.get(
        f"https://api.github.com/users/{username}/repos?per_page=100&type=owner",
        headers=HEADERS,
    )
    r.raise_for_status()
    return r.json()

def fetch_stats(username: str) -> dict:
    repos = fetch_repos(username)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    commits = prs = issues = 0

    for repo in repos:
        owner = repo["owner"]["login"]
        name = repo["name"]

        c = requests.get(
            f"https://api.github.com/repos/{owner}/{name}/commits?per_page=1",
            headers=HEADERS,
        )
        if "Link" in c.headers:
            commits += int(c.headers["Link"].split("page=")[-1].split(">")[0])
        elif c.ok:
            commits += len(c.json())

        prs += requests.get(
            f"https://api.github.com/search/issues?q=repo:{owner}/{name}+type:pr",
            headers=HEADERS,
        ).json().get("total_count", 0)

        issues += requests.get(
            f"https://api.github.com/search/issues?q=repo:{owner}/{name}+type:issue",
            headers=HEADERS,
        ).json().get("total_count", 0)

    return {"stars": stars, "commits": commits, "prs": prs, "issues": issues}

def fetch_languages(username: str) -> Counter:
    repos = fetch_repos(username)
    counter = Counter()

    for repo in repos:
        if not repo.get("languages_url"):
            continue
        r = requests.get(repo["languages_url"], headers=HEADERS)
        if r.ok:
            for lang, size in r.json().items():
                counter[lang] += size

    return counter

# ---------------- RANK ----------------
def calculate_rank(stats: dict):
    score = (
        stats["commits"] * 1.5
        + stats["prs"] * 2
        + stats["issues"] * 0.5
        + stats["stars"]
    )
    thresholds = [500, 1000, 2000, 3500, 6000]
    labels = ["C", "B", "A", "A+", "S", "S+"]

    for i, t in enumerate(thresholds):
        if score < t:
            return labels[i], (score / t) * 100
    return "S+", 100

# ---------------- SVG ----------------
def render_dashboard(user, stats, langs, theme):
    total_langs = sum(langs.values()) or 1
    top_langs = langs.most_common(5)

    rank, progress = calculate_rank(stats)
    now = datetime.utcnow().strftime("%Y-%m-%d")

    bars = []
    y = 240
    max_width = 260
    top_size = top_langs[0][1] if top_langs else 1

    for lang, size in top_langs:
        w = max(6, int(size / top_size * max_width))
        pct = size / total_langs * 100
        bars.append(f"""
        <text x="430" y="{y}" fill="{theme['text']}" font-size="12">{lang}</text>
        <rect x="510" y="{y-10}" width="{w}" height="10" rx="5"
              fill="{theme['lang_colors'].get(lang, theme['accent'])}"/>
        <text x="790" y="{y}" fill="{theme['muted']}" font-size="12">{pct:.1f}%</text>
        """)
        y += 28

    circumference = 2 * math.pi * 36
    offset = circumference * (1 - progress / 100)

    return f"""
<svg width="900" height="380" viewBox="0 0 900 380"
     xmlns="http://www.w3.org/2000/svg">

<rect width="100%" height="100%" rx="20" fill="{theme['bg']}"/>

<defs>
  <clipPath id="avatar">
    <circle cx="70" cy="70" r="40"/>
  </clipPath>
</defs>

<image href="{user['avatar_url']}" x="30" y="30" width="80" height="80"
       clip-path="url(#avatar)"/>

<text x="130" y="60" fill="{theme['title']}" font-size="22" font-weight="700">
Domisnet · Developer Dashboard
</text>

<text x="130" y="85" fill="{theme['muted']}" font-size="14">
@{user['login']} · Updated {now}
</text>

<text x="40" y="160" fill="{theme['text']}">⭐ Stars: {k(stats['stars'])}</text>
<text x="40" y="190" fill="{theme['text']}">🧠 Commits: {k(stats['commits'])}</text>
<text x="40" y="220" fill="{theme['text']}">🔀 PRs: {k(stats['prs'])}</text>
<text x="40" y="250" fill="{theme['text']}">🧩 Issues: {k(stats['issues'])}</text>

<g transform="translate(260,200)">
  <circle r="36" fill="none" stroke="{theme['track']}" stroke-width="8"/>
  <circle r="36" fill="none" stroke="{theme['accent']}" stroke-width="8"
          stroke-dasharray="{circumference}"
          stroke-dashoffset="{offset}"
          transform="rotate(-90)"/>
  <text y="8" text-anchor="middle" fill="{theme['text']}"
        font-size="22" font-weight="700">{rank}</text>
</g>

<text x="430" y="200" fill="{theme['text']}" font-size="18" font-weight="700">
Top Languages
</text>

{''.join(bars)}

</svg>
"""

# ---------------- MAIN ----------------
def main():
    import sys
    username = sys.argv[1]
    theme_name = sys.argv[2] if len(sys.argv) > 2 else "merko"
    theme = normalize_theme(theme_name)

    user = fetch_user(username)
    stats = fetch_stats(username)
    langs = fetch_languages(username)

    svg = render_dashboard(user, stats, langs, theme)

    with open("dashboard.svg", "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    main()