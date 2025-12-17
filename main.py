import os
import sys
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
        "bg": "#0047AB",
        "title": "#FFC600",
        "text": "#FFFFFF",
        "border": "#333333",
        "accent": "#FFC600",
        "bar_bg": "#0b2e66",
    },
    "dark": {
        "bg": "#151515",
        "title": "#ffffff",
        "text": "#9f9f9f",
        "border": "#e4e2e2",
        "accent": "#ffffff",
        "bar_bg": "#1e1e1e",
    },
    "dracula": {
        "bg": "#282a36",
        "title": "#f8f8f2",
        "text": "#f8f8f2",
        "border": "#44475a",
        "accent": "#ff79c6",
        "bar_bg": "#343746",
    },
    "gruvbox": {
        "bg": "#282828",
        "title": "#fabd2f",
        "text": "#ebdbb2",
        "border": "#504945",
        "accent": "#fabd2f",
        "bar_bg": "#32302f",
    },
    "merko": {
        "bg": "#0a0f0d",
        "title": "#ef553b",
        "text": "#a2a2a2",
        "border": "#ef553b",
        "accent": "#ef553b",
        "bar_bg": "#121816",
    },
    "onedark": {
        "bg": "#282c34",
        "title": "#61afef",
        "text": "#abb2bf",
        "border": "#3e4451",
        "accent": "#61afef",
        "bar_bg": "#21252b",
    },
    "radical": {
        "bg": "#141321",
        "title": "#fe428e",
        "text": "#a9fef7",
        "border": "#fe428e",
        "accent": "#fe428e",
        "bar_bg": "#1f1b2e",
    },
    "tokyonight": {
        "bg": "#1a1b27",
        "title": "#70a5fd",
        "text": "#a9b1d6",
        "border": "#414868",
        "accent": "#70a5fd",
        "bar_bg": "#222436",
    },
}

THEME = THEMES[THEME_NAME]

# ================= HELPERS =================

def safe_get(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        time.sleep(2)
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
    for r in repos:
        try:
            data = safe_get(r["languages_url"])
            for lang, val in data.items():
                counter[lang] += val
        except:
            continue
    return counter

# ================= SVG COMPONENTS =================

def render_lang_bars(counter, center_x, start_y, max_width):
    total = sum(counter.values())
    top = counter.most_common(5)

    y = start_y
    gap = 26
    bar_h = 10

    left = center_x - max_width // 2

    svg = ""

    for i, (lang, val) in enumerate(top):
        pct = (val / total) * 100
        width = max_width * (pct / 100)
        color = LANG_COLORS.get(lang, LANG_COLORS["Other"])

        delay = 0.2 + i * 0.15

        svg += f'''
<text x="{left - 12}" y="{y}" fill="{THEME['text']}"
 font-size="12" text-anchor="end">{lang}</text>

<rect x="{left}" y="{y-9}" width="{max_width}" height="{bar_h}"
 rx="5" fill="{THEME['bar_bg']}"/>

<rect x="{left}" y="{y-9}" width="0" height="{bar_h}"
 rx="5" fill="{color}">
  <animate attributeName="width"
   from="0" to="{width}"
   dur="0.8s" begin="{delay}s"
   fill="freeze"/>
</rect>

<text x="{left + max_width + 10}" y="{y}"
 fill="{THEME['text']}" font-size="12">
{pct:.1f}%
</text>
'''
        y += gap

    return svg

# ================= SVG =================

def build_svg(user, repos, langs):
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)

    return f'''
<svg width="900" height="380" xmlns="http://www.w3.org/2000/svg" opacity="0">
<animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>

<rect width="100%" height="100%" rx="28"
 fill="{THEME['bg']}"
 stroke="{THEME['border']}"
 stroke-width="4"/>

<defs>
  <radialGradient id="logoAura" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{THEME['accent']}" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="{THEME['accent']}" stop-opacity="0"/>
  </radialGradient>
</defs>

<!-- LOGO AURA -->
<circle cx="90" cy="95" r="48" fill="url(#logoAura)">
  <animate attributeName="opacity"
   from="0.35" to="0.65"
   dur="2.4s" repeatCount="indefinite"/>
</circle>

<!-- LOGO FUNDO -->
<circle cx="90" cy="95" r="34"
 fill="{THEME['bar_bg']}"/>

<circle cx="90" cy="95" r="34"
 fill="none" stroke="{THEME['accent']}" stroke-width="4"/>

<!-- </> -->
<text x="90" y="106"
 text-anchor="middle"
 fill="{THEME['accent']}"
 font-size="30"
 font-weight="bold"
 letter-spacing="5">
&lt;/&gt;
</text>

<!-- TÍTULO -->
<text x="160" y="68"
 fill="{THEME['title']}"
 font-size="22"
 font-weight="bold">
Domisnnet · Developer Dashboard
</text>

<text x="160" y="92"
 fill="{THEME['text']}"
 font-size="13">
Da faísca da ideia à Constelação do código.
</text>

<text x="160" y="112"
 fill="{THEME['text']}"
 font-size="13">
Construindo um Universo de possibilidades!!
</text>

<!-- STATS -->
<text x="160" y="145"
 fill="{THEME['text']}"
 font-size="13">
📦 {len(repos)} Repositórios · ⭐ {stars} Stars · 🍴 {forks} Forks · 🧠 {len(langs)} Linguagens
</text>

<!-- RANK -->
<circle cx="825" cy="95" r="46"
 fill="none" stroke="#2a2a2a" stroke-width="7"/>

<circle cx="825" cy="95" r="46"
 fill="none"
 stroke="{THEME['accent']}"
 stroke-width="7"
 stroke-dasharray="290"
 stroke-dashoffset="290"
 transform="rotate(-90 825 95)">
  <animate attributeName="stroke-dashoffset"
   from="290" to="30"
   dur="1.4s" fill="freeze"/>
</circle>

<text x="825" y="112"
 text-anchor="middle"
 fill="{THEME['accent']}"
 font-size="34"
 font-weight="bold">
A
</text>

<!-- TOP LANGUAGES -->
<text x="450" y="210"
 text-anchor="middle"
 fill="{THEME['accent']}"
 font-size="16"
 font-weight="bold">
Top Languages
</text>

{render_lang_bars(langs, 450, 240, 360)}

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