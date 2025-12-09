import os
import math
import logging
from collections import Counter

import requests
from flask import Flask, request, make_response
from dotenv import load_dotenv
from firebase_functions import https_fn

# As variáveis de ambiente serão configuradas diretamente no Firebase
load_dotenv()

app = Flask(__name__)

# O Cloud Functions captura logs enviados para a saída padrão
app.logger.setLevel(logging.INFO)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
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
        "title": "#fff",
        "text": "#9f9f9f",
        "icon": "#fff",
        "border": "#e4e2e2",
        "rank_circle_bg": "#333",
        "rank_circle_fill": "#fff",
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

ICONS = {
    "star": "M12 .5l3.09 6.26L22 7.77l-5 4.87 1.18 6.88L12 16.31l-6.18 3.22L7 12.64l-5-4.87 6.91-1.01L12 .5z",
    "commit": "M10.5 7.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm-2.5 3a.5.5 0 00-1 0v4.362l2.25 1.125a.5.5 0 00.5-.866L10 14.362V10.5zM15 4a1 1 0 10-2 0v1.51a3.52 3.52 0 00-1.5-.99V4a1 1 0 10-2 0v.51a3.52 3.52 0 00-1.5.99V4a1 1 0 10-2 0v.51C4.02 5.2 3 6.48 3 8v5.5a.5.5 0 001 0V8c0-1.04.5-2 1.5-2.5v2.24l-1.3.65a.5.5 0 00-.4.866l4 2a.5.5 0 00.4 0l4-2a.5.5 0 00-.4-.866l-1.3-.65V5.5C14.5 5 15 6.04 15 7v1a.5.5 0 001 0V7c0-1.52-1.02-2.8-2.5-3.49V4z",
    "pr": "M11.28 2.5a.75.75 0 00-1.06 0l-2.5 2.5a.75.75 0 000 1.06l2.5 2.5a.75.75 0 101.06-1.06L9.81 6l1.47-1.44a.75.75 0 000-1.06zm-6.56 0a.75.75 0 00-1.06 0L1.16 5.06a.75.75 0 000 1.06L3.66 8.5a.75.75 0 001.06-1.06L3.19 6l1.53-1.44a.75.75 0 00-1.06zM8 3a.75.75 0 000 1.5h.25V11a.75.75 0 001.5 0V4.5H10A.75.75 0 0010 3H8zM6 12a.75.75 0 00-1.5 0v1.25H2a.75.75 0 000 1.5h2.5a.75.75 0 00.75-.75V12z",
    "issue": "M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 118 8A8 8 0 010 8zm9-3a1 1 0 10-2 0v3a1 1 0 001 1h1a1 1 0 100-2H9V5z",
    "contrib": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 010-1.5h2V1H4.5C3.12 1 2 2.12 2 3.5V13h1.5a.75.75 0 010 1.5H2a.75.75 0 01-.75-.75V3.5h.003A2.49 2.49 0 012 2.5zM3.5 1A1.5 1.5 0 002 2.5v1.41C2.58 3.57 3.47 3.5 4.5 3.5h5V1H3.5z",
}


def k_formatter(num: int) -> str:
    return f'{num / 1000:.1f}k' if num >= 1000 else str(num)


def fetch_github_stats(username: str) -> dict | None:
    try:
        user_url = f"https://api.github.com/users/{username}"
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"

        app.logger.info(f"Fetching user data for {username}")
        u = requests.get(user_url, headers=HEADERS, timeout=10)
        u.raise_for_status()
        user = u.json()

        app.logger.info(f"Fetching repos for {username}")
        r = requests.get(repos_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        repos = r.json()

        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
        total_commits = 0
        total_prs = 0
        total_issues = 0

        for repo in repos:
            name = repo.get("name")
            owner = repo.get("owner", {}).get("login", username)

            commits_url = f"https://api.github.com/repos/{owner}/{name}/commits?per_page=1"
            prs_url = f"https://api.github.com/search/issues?q=repo:{owner}/{name}+type:pr"
            issues_url = f"https://api.github.com/search/issues?q=repo:{owner}/{name}+type:issue"

            try:
                c = requests.get(commits_url, headers=HEADERS, timeout=10)
                if "Link" in c.headers:
                    link = c.headers["Link"]
                    if 'rel="last"' in link:
                        last = link.split(",")[0].split("&page=")[-1].split(">")[0]
                        total_commits += int(last)
                elif c.ok:
                    total_commits += len(c.json())

                p = requests.get(prs_url, headers=HEADERS, timeout=10)
                if p.ok:
                    total_prs += p.json().get("total_count", 0)

                iss = requests.get(issues_url, headers=HEADERS, timeout=10)
                if iss.ok:
                    total_issues += iss.json().get("total_count", 0)
            except requests.RequestException:
                continue

        contrib_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=all"
        contrib_to = 0
        try:
            c2 = requests.get(contrib_url, headers=HEADERS, timeout=10)
            if c2.ok:
                all_repos = c2.json()
                contrib_to = sum(
                    1 for repo in all_repos
                    if repo.get("owner", {}).get("login") != username
                )
        except requests.RequestException:
            pass

        return {
            "name": user.get("name") or user.get("login"),
            "total_stars": total_stars,
            "total_commits": total_commits,
            "total_prs": total_prs,
            "total_issues": total_issues,
            "contrib_to": contrib_to,
        }
    except requests.RequestException as e:
        app.logger.error(f"Error fetching GitHub stats: {e}")
        return None


def calculate_rank(stats: dict) -> dict:
    score = (
        stats.get("total_commits", 0) * 1.5
        + stats.get("total_prs", 0) * 2.0
        + stats.get("total_issues", 0) * 0.5
        + stats.get("total_stars", 0) * 1.0
        + stats.get("contrib_to", 0) * 2.5
    )

    THRESHOLDS = {
        "S++": 6000,
        "S+": 5000,
        "S": 4000,
        "A++": 3000,
        "A+": 2000,
        "A": 1000,
        "B+": 500,
        "B": 200,
    }
    RANK_ORDER = ["C", "B", "B+", "A", "A+", "A++", "S", "S+", "S++"]

    level = "C"
    for r, threshold in sorted(THRESHOLDS.items(), key=lambda item: item[1]):
        if score >= threshold:
            level = r

    current_index = RANK_ORDER.index(level)
    lower = THRESHOLDS.get(level, 0) if level != "C" else 0
    upper = (
        THRESHOLDS.get(RANK_ORDER[current_index + 1], lower * 2)
        if current_index + 1 < len(RANK_ORDER)
        else lower * 1.5
    )
    progress = ((score - lower) / (upper - lower) * 100) if upper > lower else 0
    return {"level": level, "progress": max(0, min(100, progress))}


def create_stats_svg(stats: dict, theme_name: str = "tokyonight") -> str:
    theme = THEMES.get(theme_name, THEMES["tokyonight"])
    if not stats:
        return f'''
<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{theme['background']}" rx="5" ry="5"/>
  <text x="50%" y="50%" fill="#ff4a4a" text-anchor="middle"
        font-family="Segoe UI, Ubuntu, Sans-Serif">Failed to fetch GitHub stats</text>
</svg>
'''.strip()

    rank = calculate_rank(stats)

    width, height = 495, 195
    padding = 20

    stat_items = {
        "Total Stars": stats.get("total_stars", 0),
        "Total Commits": stats.get("total_commits", 0),
        "Total PRs": stats.get("total_prs", 0),
        "Total Issues": stats.get("total_issues", 0),
        "Contributed to": stats.get("contrib_to", 0),
    }

    icons = [
        ICONS["star"],
        ICONS["commit"],
        ICONS["pr"],
        ICONS["issue"],
        ICONS["contrib"],
    ]

    stats_svg = ""
    for i, (label, value) in enumerate(stat_items.items()):
        icon_svg = f'''
<svg x="0" y="{i * 25}" width="16" height="16" viewBox="0 0 24 24"
     fill="{theme['icon']}" xmlns="http://www.w3.org/2000/svg">
  <path d="{icons[i]}"/>
</svg>
'''
        text_svg = f'''
<text x="25" y="{i * 25 + 12}" fill="{theme['text']}"
      font-size="14" font-family="Segoe UI, Ubuntu, Sans-Serif">
  <tspan font-weight="bold">{label}:</tspan>
  <tspan x="150" text-anchor="start">{k_formatter(value)}</tspan>
</text>
'''
        stats_svg += f"<g>{icon_svg}{text_svg}</g>\n"

    radius = 50
    cx, cy = radius, radius
    circumference = 2 * math.pi * radius
    offset = circumference - (rank["progress"] / 100 * circumference)

    rank_circle_svg = f'''
<g>
  <circle r="{radius}" cx="{cx}" cy="{cy}" fill="none"
          stroke="{theme['rank_circle_bg']}" stroke-width="10"/>
  <circle r="{radius}" cx="{cx}" cy="{cy}" fill="none"
          stroke="{theme['rank_circle_fill']}" stroke-width="10"
          stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
          stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy + 10}" text-anchor="middle"
        fill="{theme['text']}" font-size="28" font-weight="bold"
        font-family="Segoe UI, Ubuntu, Sans-Serif">{rank['level']}</text>
</g>
'''

    svg = f'''
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{
      font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif;
      fill: {theme['title']};
    }}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" height="99%" width="{width - 1}"
        fill="{theme['background']}" stroke="{theme['border']}"
  />
  <g transform="translate({padding}, {padding})">
    <text x="0" y="18" class="header">{stats['name']}\'s GitHub Stats</text>
    <g transform="translate(0, 40)">{stats_svg}</g>
    <g transform="translate(320, 30)">{rank_circle_svg}</g>
  </g>
</svg>
'''
    return svg.strip()


def create_language_donut_chart_svg(
    langs: Counter, theme_name: str = "tokyonight"
) -> str:
    theme = THEMES.get(theme_name, THEMES["tokyonight"])
    if not langs:
        return f'''
<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{theme['background']}" rx="5" ry="5"/>
  <text x="50%" y="50%" fill="#ff4a4a" text-anchor="middle"
        font-family="Segoe UI, Ubuntu, Sans-Serif">Failed to fetch language data</text>
</svg>
'''.strip()

    total_size = sum(langs.values())
    top_langs = langs.most_common(6)

    paths = []
    legend_items = ""
    start_angle = -90

    for i, (lang, size) in enumerate(top_langs):
        percent = (size / total_size) * 100
        angle = (size / total_size) * 360
        end_angle = start_angle + angle
        large_arc_flag = 1 if angle > 180 else 0

        x1_outer = 225 + 50 * math.cos(math.radians(start_angle))
        y1_outer = 90 + 50 * math.sin(math.radians(start_angle))
        x2_outer = 225 + 50 * math.cos(math.radians(end_angle))
        y2_outer = 90 + 50 * math.sin(math.radians(end_angle))

        x1_inner = 225 + 30 * math.cos(math.radians(start_angle))
        y1_inner = 90 + 30 * math.sin(math.radians(start_angle))
        x2_inner = 225 + 30 * math.cos(math.radians(end_angle))
        y2_inner = 90 + 30 * math.sin(math.radians(end_angle))

        color = theme["lang_colors"].get(lang, "#ededed")
        path_d = (
            f"M {x1_outer} {y1_outer} A 50 50 0 {large_arc_flag} 1 {x2_outer} {y2_outer} "
            f"L {x2_inner} {y2_inner} A 30 30 0 {large_arc_flag} 0 {x1_inner} {y1_inner} Z"
        )
        paths.append(f'<path d="{path_d}" fill="{color}" />')

        legend_items += f'''
<g transform="translate(20, {50 + i * 20})">
  <rect width="10" height="10" fill="{color}" rx="2" ry="2"/>
  <text x="15" y="10" font-family="Segoe UI, Ubuntu, Sans-Serif"
        font-size="12" fill="{theme['text']}"> {lang} ({percent:.1f}%)</text>
</g>
'''

        start_angle = end_angle

    return f'''
<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <rect width="493" height="193" x="1" y="1" rx="5" ry="5"
        fill="{theme['background']}" stroke="{theme['border']}"
  />
  <text x="20" y="30" font-family="Segoe UI, Ubuntu, Sans-Serif"
        font-size="18" font-weight="bold" fill="{theme['title']}">Top Languages</text>
  <g transform="translate(200, 0)">{' '.join(paths)}</g>
  <g>{legend_items}</g>
</svg>
'''.strip()


def fetch_top_languages(username: str) -> Counter | None:
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"
    try:
        app.logger.info(f"Fetching repos for top languages of {username}")
        r = requests.get(repos_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        repos = r.json()

        lang_stats: Counter = Counter()
        for repo in repos:
            lang_url = repo.get("languages_url")
            if not lang_url:
                continue
            try:
                lr = requests.get(lang_url, headers=HEADERS, timeout=10)
                if not lr.ok:
                    continue
                for lang, size in lr.json().items():
                    lang_stats[lang] += size
            except requests.RequestException:
                continue

        return lang_stats
    except requests.RequestException as e:
        app.logger.error(f"Error fetching top languages: {e}")
        return None


@app.route("/api/stats")
def api_stats():
    username = request.args.get("username", "Domisnnet")
    theme = request.args.get("theme", "tokyonight")
    stats = fetch_github_stats(username)
    svg = create_stats_svg(stats, theme)
    resp = make_response(svg)
    resp.headers["Content-Type"] = "image/svg+xml"
    resp.headers["Cache-Control"] = "s-maxage=3600, stale-while-revalidate"
    return resp


@app.route("/api/top-langs")
def api_top_langs():
    username = request.args.get("username", "Domisnnet")
    theme = request.args.get("theme", "tokyonight")
    langs = fetch_top_languages(username)
    svg = create_language_donut_chart_svg(langs or Counter(), theme)
    resp = make_response(svg)
    resp.headers["Content-Type"] = "image/svg+xml"
    resp.headers["Cache-Control"] = "s-maxage=3600, stale-while-revalidate"
    return resp

@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()