from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, functions
import requests
import json

set_global_options(max_instances=10)

initialize_app()

@https_fn.on_request()
def getItems(req: https_fn.Request):
    path = req.path  # ex: /dashboard

    if path != "/dashboard":
        return https_fn.Response(
            json.dumps({"error": "Endpoint inválido"}),
            status=404,
            content_type="application/json"
        )

    username = req.args.get("username")
    theme = req.args.get("theme", "default")

    if not username:
        return https_fn.Response(
            json.dumps({"error": "Parâmetro username é obrigatório"}),
            status=400,
            content_type="application/json"
        )

    # Token vindo do Firebase config
    config = functions.config()
    github_token = config.github.token

    headers = {
        "Accept": "application/vnd.github+json"
    }

    if github_token:
        headers["Authorization"] = f"token {github_token}"

    try:
        r = requests.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
            timeout=10
        )

        if r.status_code != 200:
            return https_fn.Response(
                json.dumps({"error": "Usuário GitHub não encontrado"}),
                status=404,
                content_type="application/json"
            )

        user = r.json()

        response = {
            "username": username,
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "public_repos": user.get("public_repos"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "theme": theme
        }

        return https_fn.Response(
            json.dumps(response),
            content_type="application/json"
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500,
            content_type="application/json"
        )