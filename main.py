import os
import sys
import time
import requests
from collections import Counter
from dotenv import load_dotenv
from flask import Flask, request, send_from_directory, Response

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

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

app = Flask(__name__, static_folder='public')

# ================= HELPERS =================

def safe_get(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 429:
        # Wait for the rate limit to reset
        reset_time = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait_time = max(reset_time - time.time(), 1)
        app.logger.warning(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
        time.sleep(wait_time)
        return safe_get(url) # Retry the request
    
    r.raise_for_status() # Raise an exception for other bad statuses (404, 500, etc.)
    return r.json()

# ================= FETCH =================

def fetch_user_repos_and_langs(username):
    app.logger.info(f"Fetching data for user: {username}")
    user = safe_get(f"https://api.github.com/users/{username}")
    repos = safe_get(f"https://api.github.com/users/{username}/repos?per_page=100&type=owner")
    
    counter = Counter()
    for r in repos:
        try:
            if r.get("languages_url"):
                data = safe_get(r["languages_url"])
                for lang, val in data.items():
                    counter[lang] += val
        except Exception as e:
            app.logger.warning(f"Could not fetch languages for repo {r.get('name')}: {e}")
            continue
    app.logger.info(f"Finished fetching data for user: {username}")
    return user, repos, counter

# ================= SVG COMPONENTS =================

def render_lang_bars(counter, center_x, start_y, max_width, theme):
    total = sum(counter.values())
    if total == 0:
        return f'<text x="{center_x}" y="{start_y}" fill="{theme["text"]}" text-anchor="middle" font-size="14">No language data available.</text>' 
        
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
<text x="{left - 12}" y="{y}" fill="{theme['text']}" font-size="12" text-anchor="end">{lang}</text>
<rect x="{left}" y="{y-9}" width="{max_width}" height="{bar_h}" rx="5" fill="{theme['bar_bg']}"/>
<rect x="{left}" y="{y-9}" width="0" height="{bar_h}" rx="5" fill="{color}">
  <animate attributeName="width" from="0" to="{width}" dur="0.8s" begin="{delay}s" fill="freeze"/>
</rect>
<text x="{left + max_width + 10}" y="{y}" fill="{theme['text']}" font-size="12">{pct:.1f}%</text>
'''
        y += gap
    return svg

# ================= SVG (COMBINED) =================

def build_combined_svg(user, repos, langs, theme):
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)
    user_name = user.get('name') or user.get('login', 'GitHub User')

    return f'''
<svg width="900" height="380" xmlns="http://www.w3.org/2000/svg" opacity="0">
<animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>
<rect width="100%" height="100%" rx="28" fill="{theme['bg']}" stroke="{theme['border']}" stroke-width="4"/>
<defs>
  <radialGradient id="logoAura" cx="50%" cy="50%" r="60%">
    <stop offset="0%" stop-color="{theme['accent']}" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="{theme['accent']}" stop-opacity="0"/>
  </radialGradient>
</defs>
<circle cx="90" cy="95" r="48" fill="url(#logoAura)"><animate attributeName="opacity" from="0.35" to="0.65" dur="2.4s" repeatCount="indefinite"/></circle>
<circle cx="90" cy="95" r="34" fill="{theme['bar_bg']}"/>
<circle cx="90" cy="95" r="34" fill="none" stroke="{theme['accent']}" stroke-width="4"/>
<text x="90" y="106" text-anchor="middle" fill="{theme['accent']}" font-size="30" font-weight="bold" letter-spacing="5">&lt;/&gt;</text>
<text x="160" y="68" fill="{theme['title']}" font-size="22" font-weight="bold">{user_name} · Developer Dashboard</text>
<text x="160" y="92" fill="{theme['text']}" font-size="13">Da faísca da ideia à Constelação do código.</text>
<text x="160" y="112" fill="{theme['text']}" font-size="13">Construindo um Universo de possibilidades!!</text>
<text x="160" y="145" fill="{theme['text']}" font-size="13">📦 {len(repos)} Repositórios · ⭐ {stars} Stars · 🍴 {forks} Forks · 🧠 {len(langs)} Linguagens</text>
<circle cx="825" cy="95" r="46" fill="none" stroke="#2a2a2a" stroke-width="7"/>
<circle cx="825" cy="95" r="46" fill="none" stroke="{theme['accent']}" stroke-width="7" stroke-dasharray="290" stroke-dashoffset="290" transform="rotate(-90 825 95)"><animate attributeName="stroke-dashoffset" from="290" to="30" dur="1.4s" fill="freeze"/></circle>
<text x="825" y="112" text-anchor="middle" fill="{theme['accent']}" font-size="34" font-weight="bold">A</text>
<text x="450" y="210" text-anchor="middle" fill="{theme['accent']}" font-size="16" font-weight="bold">Top Languages</text>
{render_lang_bars(langs, 450, 240, 360, theme)}
</svg>
'''

# ================= FLASK ROUTES =================

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/dashboard')
def dashboard():
    username = request.args.get('username')
    theme_name = request.args.get('theme', 'merko')
    theme = THEMES.get(theme_name, THEMES['merko'])
    
    if not username:
        return "Missing username", 400

    try:
        user, repos, langs = fetch_user_repos_and_langs(username)
        svg = build_combined_svg(user, repos, langs, theme)
        return Response(svg, mimetype='image/svg+xml', headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        })
    except requests.exceptions.HTTPError as e:
        return f"Error fetching data from GitHub: {e}", 502
    except Exception as e:
        return "An internal error occurred", 500

# ================= MAIN =================

def generate_and_save_svg(username):
    theme_name = os.getenv("THEME_NAME", "merko")
    theme = THEMES.get(theme_name, THEMES['merko'])
    try:
        print(f"Fetching data for {username}...")
        user, repos, langs = fetch_user_repos_and_langs(username)
        
        print("Building combined SVG...")
        svg_content = build_combined_svg(user, repos, langs, theme)

        with open("dashboard.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Successfully generated dashboard.svg for {username}")
    except Exception as e:
        print(f"Error generating SVG: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        generate_and_save_svg(username)
    else:
        app.run(host='0.0.0.0', port=8080, debug=True)
