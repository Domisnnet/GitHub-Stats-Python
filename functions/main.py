from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
import json

set_global_options(max_instances=10)
initialize_app()

@https_fn.on_request()
def getItems(req: https_fn.Request):
    return https_fn.Response(
        json.dumps({"status": "ok"}),
        content_type="application/json"
    )