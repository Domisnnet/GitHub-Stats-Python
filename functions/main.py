from firebase_functions import https_fn, scheduler_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
from collections import Counter
from datetime import datetime
import requests
import hashlib
import os

# ======================================================
# CONFIGURAÇÃO GLOBAL
# ======================================================

set_global_options(region="us-central1", max_instances=10)
initialize_app()

db = firestore.client()

GITHUB_USERNAME = "Domisnnet"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

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

# ======================================================
# HELPERS
# ======================================================

def make_etag(svg: str) -> str:
    return hashlib.md5(svg.encode("utf-8")).hexdigest()

# ======================================================
# SYNC — GITHUB → FIRESTORE (FONTE DA VERDADE)
# ======================================================

@scheduler_fn.on_schedule(schedule="every 24 hours")
def sync_github_data(event):
    repos = []
    page = 1

    # Busca TODOS os repositórios (paginação correta)
    while True:
        resp = requests.get(
            f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page}
        )

        if resp.status_code != 200:
            raise RuntimeError("Erro ao buscar repositórios do GitHub")

        data = resp.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    langs_counter = Counter()
    repos_data = []

    for repo in repos:
        # Ignora forks (boa prática)
        if repo["fork"]:
            continue

        # Linguagens reais por bytes
        lang_resp = requests.get(repo["languages_url"], headers=HEADERS)
        if lang_resp.status_code == 200:
            for lang, size in lang_resp.json().items():
                langs_counter[lang] += size

        repos_data.append({
            "name": repo["name"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "issues": repo["open_issues_count"]
        })

    # Limpa coleção antiga
    batch = db.batch()
    repos_ref = db.collection("repos")

    for doc in repos_ref.stream():
        batch.delete(doc.reference)

    # Salva repos atualizados
    for repo in repos_data:
        batch.set(repos_ref.document(repo["name"]), repo)

    # Metadata do sync
    batch.set(
        db.collection("meta").document("sync"),
        {"last_sync": firestore.SERVER_TIMESTAMP}
    )

    # Linguagens agregadas
    batch.set(
        db.collection("stats").document("languages"),
        {"data": dict(langs_counter)}
    )

    batch.commit()

    print(f"SYNC OK — {len(repos_data)} repositórios processados")

# ======================================================
# SVG — LEITURA APENAS DO FIRESTORE
# ======================================================

@https_fn.on_request()
def statsSvg(req):
    theme = THEMES["merko"]

    repos_docs = db.collection("repos").stream()
    langs_doc = db.collection("stats").document("languages").get()
    meta_doc = db.collection("meta").document("sync").get()

    repos = [doc.to_dict() for doc in repos_docs]
    langs = Counter(langs_doc.to_dict().get("data", {})) if langs_doc.exists else Counter()

    stars = sum(r["stars"] for r in repos)
    forks = sum(r["forks"] for r in repos)

    last_sync = meta_doc.to_dict().get("last_sync") if meta_doc.exists else None
    last_sync_str = last_sync.strftime("%Y-%m-%d %H:%M UTC") if last_sync else "never"

    total_langs = sum(langs.values()) or 1
    top_langs = langs.most_common(5)

    # --------------------------------------------------
    # SVG
    # --------------------------------------------------

    svg = f"""
<svg viewBox="0 0 900 380" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="28"
        fill="{theme['bg']}" stroke="{theme['border']}" stroke-width="4"/>

  <text x="160" y="70" fill="{theme['title']}"
        font-size="22" font-weight="bold">
    DomisDev · Developer Dashboard
  </text>

  <text x="160" y="105" fill="{theme['text']}" font-size="13">
    📦 {len(repos)} Repositórios · ⭐ {stars} Stars · 🍴 {forks} Forks
  </text>

  <text x="450" y="165" text-anchor="middle"
        fill="{theme['accent']}" font-size="16" font-weight="bold">
    Top Languages
  </text>
"""

    y = 200
    for lang, size in top_langs:
        pct = (size / total_langs) * 100
        color = LANG_COLORS.get(lang, LANG_COLORS["Other"])
        width = int(pct * 3)

        svg += f"""
  <text x="260" y="{y}" fill="{theme['text']}" font-size="12">{lang}</text>
  <rect x="340" y="{y - 10}" width="{width}" height="10"
        rx="5" fill="{color}"/>
  <text x="700" y="{y}" fill="{theme['text']}" font-size="12">
    {pct:.1f}%
  </text>
"""
        y += 26

    svg += f"""
  <text x="450" y="355" text-anchor="middle"
        fill="{theme['text']}" font-size="11">
    Last sync: {last_sync_str}
  </text>
</svg>
"""

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