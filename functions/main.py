from firebase_functions import https_fn, scheduler_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
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

    # Exemplo simples: usuário fixo (ajustável depois)
    username = "Domisnnet"

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
            "updated_at": repo["updated_at"]
        })

    batch.commit()

    return len(repos)


# =========================
# HTTP (MANUAL)
# =========================
@https_fn.on_request()
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
@scheduler_fn.on_schedule(schedule="every 24 hours")
def syncGithubDaily(event):
    try:
        total = sync_github()
        print(f"Repos sincronizados automaticamente: {total}")
    except Exception as e:
        print(f"Erro no cron: {str(e)}")