from firebase_functions import https_fn, scheduler_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
from collections import Counter
from datetime import datetime
import requests
import os

# Limite de instâncias
set_global_options(max_instances=10)

# Inicializa Firebase Admin
initialize_app()

# =========================
# LÓGICA CENTRAL
# =========================
def sync_github():
    db = firestore.client()

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise Exception("GITHUB_TOKEN não configurado")

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    username = os.environ.get("GITHUB_USERNAME", "Domisnnet")

    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Erro GitHub API: {response.text}")

    repos = response.json()

    batch = db.batch()
    for repo in repos:
        ref = db.collection("repos").document(str(repo["id"]))
        batch.set(ref, {
            "name": repo["name"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "language": repo["language"],
            "url": repo["html_url"],
            "updated_at": repo["updated_at"]
        })

    batch.commit()

    return len(repos)


# =========================
# HTTP (MANUAL)
# =========================
@https_fn.on_request(secrets=["GITHUB_TOKEN"])
def syncGithubHttp(req):
    try:
        total = sync_github()
        return {
            "success": True,
            "synced_repos": total
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500


# =========================
# CRON (AUTOMÁTICO)
# =========================
@scheduler_fn.on_schedule(
    schedule="every 24 hours",
    secrets=["GITHUB_TOKEN"]
)
def syncGithubDaily(event):
    try:
        total = sync_github()
        print(f"Repos sincronizados automaticamente: {total}")
    except Exception as e:
        print(f"Erro no cron: {str(e)}")

# =========================
# DASHBOARD
# =========================

@https_fn.on_request()
def dashboard(req):
    try:
        db = firestore.client()

        docs = db.collection("repos").stream()

        total_stars = 0
        total_forks = 0
        repo_count = 0
        languages = []
        repos = []

        for doc in docs:
            data = doc.to_dict()
            repo_count += 1

            stars = data.get("stars", 0)
            forks = data.get("forks", 0)
            language = data.get("language")

            total_stars += stars
            total_forks += forks

            if language:
                languages.append(language)

            repos.append({
                "name": data.get("name"),
                "stars": stars,
                "url": data.get("url")
            })

        top_languages = Counter(languages).most_common(5)
        top_repos = sorted(repos, key=lambda x: x["stars"], reverse=True)[:5]

        return {
            "success": True,
            "summary": {
                "repos": repo_count,
                "stars": total_stars,
                "forks": total_forks
            },
            "top_languages": [
                {"language": lang, "count": count}
                for lang, count in top_languages
            ],
            "top_repos": top_repos,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500
        
# =========================
# STATS SVG
# =========================

@https_fn.on_request()
def statsSvg(req):
    try:
        db = firestore.client()
        docs = db.collection("repos").stream()

        total_stars = 0
        total_forks = 0
        repo_count = 0
        languages = []

        for doc in docs:
            data = doc.to_dict()
            repo_count += 1
            total_stars += data.get("stars", 0)
            total_forks += data.get("forks", 0)

            if data.get("language"):
                languages.append(data["language"])

        top_languages = Counter(languages).most_common(3)

        svg = f"""
<svg width="420" height="160" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{
      font-family: 'Segoe UI', Arial, sans-serif;
      fill: #e6edf3;
    }}
    .title {{
      font-size: 16px;
      font-weight: bold;
    }}
    .stat {{
      font-size: 14px;
    }}
    .lang {{
      font-size: 12px;
      fill: #9da5b4;
    }}
  </style>

  <rect width="100%" height="100%" rx="12" fill="#0d1117"/>

  <text x="20" y="28" class="title">GitHub Stats</text>

  <text x="20" y="60" class="stat">📦 Repositórios: {repo_count}</text>
  <text x="20" y="82" class="stat">⭐ Stars: {total_stars}</text>
  <text x="20" y="104" class="stat">🍴 Forks: {total_forks}</text>

  <text x="20" y="134" class="lang">
    Top linguagens: {", ".join(lang for lang, _ in top_languages)}
  </text>
</svg>
"""

        return https_fn.Response(
            svg,
            headers={
                "Content-Type": "image/svg+xml",
                "Cache-Control": "public, max-age=3600"
            }
        )

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500