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

USERNAME = sys.argv[1] if len(sys.argv) > 1 else None
if not USERNAME:
    sys.exit(1)

TOKEN = os.getenv("GITHUB_TOKEN")
THEME_NAME = os.getenv("THEME_NAME", "merko")

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})
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
    "Other": "#ededed",
}

THEMES = {
    "cobalt": {"background":"#0047AB","title":"#FFC600","text":"#FFFFFF","icon":"#FFC600","border":"#333","rank_circle_bg":"#333","rank_circle_fill":"#FFC600","lang_colors":LANG_COLORS},
    "dark": {"background":"#151515","title":"#ffffff","text":"#9f9f9f","icon":"#ffffff","border":"#e4e2e2","rank_circle_bg":"#333","rank_circle_fill":"#ffffff","lang_colors":LANG_COLORS},
    "dracula": {"background":"#282a36","title":"#f8f8f2","text":"#f8f8f2","icon":"#f8f8f2","border":"#44475a","rank_circle_bg":"#44475a","rank_circle_fill":"#ff79c6","lang_colors":LANG_COLORS},
    "gruvbox": {"background":"#282828","title":"#fabd2f","text":"#ebdbb2","icon":"#fabd2f","border":"#504945","rank_circle_bg":"#504945","rank_circle_fill":"#fabd2f","lang_colors":LANG_COLORS},
    "merko": {"background":"#0a0f0d","title":"#ef553b","text":"#a2a2a2","icon":"#ef553b","border":"#ef553b","rank_circle_bg":"#2d2d2d","rank_circle_fill":"#ef553b","lang_colors":LANG_COLORS},
    "onedark": {"background":"#282c34","title":"#61afef","text":"#abb2bf","icon":"#61afef","border":"#3e4451","rank_circle_bg":"#3e4451","rank_circle_fill":"#61afef","lang_colors":LANG_COLORS},
    "radical": {"background":"#141321","title":"#fe428e","text":"#a9fef7","icon":"#fe428e","border":"#fe428e","rank_circle_bg":"#54253a","rank_circle_fill":"#fe428e","lang_colors":LANG_COLORS},
    "tokyonight": {"background":"#1a1b27","title":"#70a5fd","text":"#a9b1d6","icon":"#70a5fd","border":"#414868","rank_circle_bg":"#414868","rank_circle_fill":"#70a5fd","lang_colors":LANG_COLORS},
}

THEME = THEMES.get(THEME_NAME, THEMES["merko"])

def safe_get(url, delay=0.35):
    time.sleep(delay)
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 429:
        logging.warning("Rate limit atingido. Execução encerrada com segurança.")
        sys.exit(0)
    r.raise_for_status()
    return r.json(), r.headers

# -------- FETCH (cache único) --------
CACHE = {}

def fetch_repos():
    if "repos" not in CACHE:
        CACHE["repos"], _ = safe_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")
    return CACHE["repos"]

def fetch_user():
    if "user" not in CACHE:
        CACHE["user"], _ = safe_get(f"https://api.github.com/users/{USERNAME}")
    return CACHE["user"]

def fetch_languages():
    if "langs" in CACHE:
        return CACHE["langs"]
    counter = Counter()
    for repo in fetch_repos():
        if repo.get("languages_url"):
            try:
                langs, _ = safe_get(repo["languages_url"], delay=0.2)
                for l, s in langs.items():
                    counter[l] += s
            except Exception:
                pass
    CACHE["langs"] = counter
    return counter

# -------- SCORE / RANK --------
def calc_rank(repos, langs):
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    repo_count = len(repos)
    lang_div = len(langs)

    score = stars * 2 + repo_count * 10 + lang_div * 15
    levels = [("C",0),("B",200),("B+",400),("A",700),("A+",1000),("S",1400),("S+",1800),("S++",2300)]
    level = "C"
    lower = 0
    upper = levels[-1][1]
    for i,(l,v) in enumerate(levels):
        if score >= v:
            level = l
            lower = v
            upper = levels[i+1][1] if i+1 < len(levels) else v*1.2
    progress = min(100, max(0, (score-lower)/(upper-lower)*100 if upper>lower else 0))
    return level, progress

# -------- SVG BUILDERS --------
def avatar_svg(cx, cy, r):
    return f"""
<g>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{THEME['rank_circle_bg']}"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
          stroke="{THEME['rank_circle_fill']}" stroke-width="2"/>
  <text x="{cx}" y="{cy+10}" text-anchor="middle"
        font-size="26" fill="{THEME['icon']}"
        font-family="Segoe UI, Ubuntu, Sans-Serif"
        font-weight="bold">&lt;/&gt;</text>
</g>
"""

def dashboard_svg(user, repos, langs):
    level, prog = calc_rank(repos, langs)
    R = 42
    C = 2*math.pi*R
    offset = C - (prog/100)*C

    top_langs = langs.most_common(5)
    total = sum(langs.values()) or 1
    bars = ""
    x = 40
    for l,s in top_langs:
        w = int((s/total)*420)
        color = THEME["lang_colors"].get(l, "#ccc")
        bars += f'<rect x="{x}" y="200" width="{w}" height="14" rx="7" fill="{color}"/>\n'
        x += w

    return f"""
<svg width="700" height="260" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="24"
        fill="{THEME['background']}"
        stroke="{THEME['border']}"
        stroke-width="2.5"/>

  {avatar_svg(60,60,28)}

  <text x="110" y="45" font-size="22" fill="{THEME['title']}"
        font-family="Segoe UI, Ubuntu, Sans-Serif" font-weight="bold">
    Domisnnet · Developer Dashboard
  </text>

  <text x="110" y="70" font-size="13" fill="{THEME['text']}" opacity="0.85"
        font-family="Segoe UI, Ubuntu, Sans-Serif">
    Da faísca da ideia à Constelação do código.
  </text>
  <text x="110" y="88" font-size="13" fill="{THEME['text']}" opacity="0.65"
        font-family="Segoe UI, Ubuntu, Sans-Serif">
    Construindo um Universo de possibilidades!!
  </text>

  <!-- Rank -->
  <g transform="translate(560,50)">
    <circle r="{R}" cx="0" cy="0" fill="none"
            stroke="{THEME['rank_circle_bg']}" stroke-width="9"/>
    <circle r="{R}" cx="0" cy="0" fill="none"
            stroke="{THEME['rank_circle_fill']}" stroke-width="9"
            stroke-dasharray="{C}" stroke-dashoffset="{offset}"
            stroke-linecap="round"
            transform="rotate(-90)"/>
    <text x="0" y="8" text-anchor="middle"
          font-size="22" fill="{THEME['text']}"
          font-family="Segoe UI, Ubuntu, Sans-Serif"
          font-weight="bold">{level}</text>
  </g>

  <!-- Stats -->
  <text x="40" y="130" fill="{THEME['text']}" font-size="14"
        font-family="Segoe UI, Ubuntu, Sans-Serif">
    Repositórios: {len(repos)} · Stars: {sum(r.get("stargazers_count",0) for r in repos)}
  </text>

  <text x="40" y="155" fill="{THEME['title']}" font-size="16"
        font-family="Segoe UI, Ubuntu, Sans-Serif" font-weight="bold">
    Top Languages
  </text>

  {bars}
</svg>
""".strip()

def main():
    user = fetch_user()
    repos = fetch_repos()
    langs = fetch_languages()

    svg = dashboard_svg(user, repos, langs)
    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    main()