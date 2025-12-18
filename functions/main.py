from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
import requests
import json
import os

set_global_options(max_instances=10)

initialize_app()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

@https_fn.on_request()
def getItems(req: https_fn.Request):
    path = req.path

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
            json.dumps({"error": "username é obrigatório"}),
            status=400,
            content_type="application/json"
        )

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        user_resp = requests.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
            timeout=10
        )

        if user_resp.status_code != 200:
            return https_fn.Response(
                json.dumps({"error": "Usuário não encontrado"}),
                status=404,
                content_type="application/json"
            )

        user = user_resp.json()

        data = {
            "username": username,
            "name": user.get("name"),
            "public_repos": user.get("public_repos"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "theme": theme
        }

        return https_fn.Response(
            json.dumps(data),
            content_type="application/json"
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500,
            content_type="application/json"
        )