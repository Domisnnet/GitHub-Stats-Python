from firebase_functions import https_fn, scheduler_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
from collections import Counter
from datetime import datetime
import hashlib
import requests
import os

# =========================
# CONFIGURAÇÃO GLOBAL
# =========================

set_global_options(max_instances=10)
initialize_app()

db = firestore.client()

GITHUB_API = "https://api.github.com"
GITHUB_USERNAME = "Domisnnet"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# =========================
# CORES POR LINGUAGEM
# =========================

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
    "Vue": "#41b883",
    "Other": "#ededed",
}

# =========================
# TEMAS
# =========================

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

# =========================
# HELPERS
# =========================

def github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def make_etag(svg: str) -> str:
    return hashlib.md5(svg.encode("utf-8")).hexdigest()

# =========================
# SVG COMPONENTES
# =========================

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

def build_combined_svg(user, repos, langs, theme):
    stars = sum(r.get("stars", 0) for r in repos)
    forks = sum(r.get("forks", 0) for r in repos)
    user_name = user.get("name") or user.get("login", "GitHub User")

    return f'''
<svg viewBox="0 0 900 380" xmlns="http://www.w3.org/2000/svg" opacity="0">
<style>
.stat-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
</style>
<animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>
<rect width="100%" height="100%" rx="28" fill="{theme['bg']}" stroke="{theme['border']}" stroke-width="4"/>
<text x="160" y="68" fill="{theme['title']}" font-size="22" font-weight="bold">{user_name} · Developer Dashboard</text>
<text x="160" y="145" fill="{theme['text']}" font-size="13">
📦 {len(repos)} Repositórios · ⭐ {stars} Stars · 🍴 {forks} Forks · 🧠 {len(langs)} Linguagens
</text>
<text x="450" y="210" text-anchor="middle" fill="{theme['accent']}" font-size="16" font-weight="bold">Top Languages</text>
{render_lang_bars(langs, 450, 240, 360, theme)}
</svg>
'''

# =========================
# SYNC GITHUB → FIRESTORE
# =========================

@scheduler_fn.on_schedule(schedule="every 24 hours")
def sync_github_data(event):
    repos_url = f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos?per_page=100"
    resp = requests.get(repos_url, headers=github_headers())
    resp.raise_for_status()

    repos_data = resp.json()

    batch = db.batch()
    repos_ref = db.collection("repos")

    for doc in repos_ref.stream():
        batch.delete(doc.reference)

    for repo in repos_data:
        batch.set(repos_ref.document(str(repo["id"])), {
            "name": repo["name"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "language": repo["language"],
            "updated_at": repo["updated_at"]
        })

    batch.commit()
    print(f"Sync OK: {len(repos_data)} repositórios")

# =========================
# SVG HTTP FUNCTION
# =========================

@https_fn.on_request()
def statsSvg(req):
    theme_name = req.args.get("theme", "tokyonight")
    theme = THEMES.get(theme_name, THEMES["tokyonight"])

    repos_docs = db.collection("repos").stream()
    repos = []
    langs = Counter()

    for doc in repos_docs:
        data = doc.to_dict()
        repos.append(data)
        if data.get("language"):
            langs[data["language"]] += 1

    user = {"name": GITHUB_USERNAME, "login": GITHUB_USERNAME}

    svg = build_combined_svg(user, repos, langs, theme)
    etag = make_etag(svg)

    if req.headers.get("If-None-Match") == etag:
        return https_fn.Response(status=304)

    return https_fn.Response(
        svg,
        headers={
            "Content-Type": "image/svg+xml; charset=utf-8",
            "Cache-Control": "no-cache",
            "ETag": etag
        }
    )