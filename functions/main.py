from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
import json

set_global_options(max_instances=10)
initialize_app()

@https_fn.on_request()
def getItems(req: https_fn.Request):
    try:
        db = firestore.client()
        docs = db.collection("items").stream()

        data = []
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)

        return https_fn.Response(
            json.dumps({
                "success": True,
                "data": data
            }),
            content_type="application/json"
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            status=500,
            content_type="application/json"
        )