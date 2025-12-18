from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore

# Limite de instâncias
set_global_options(max_instances=10)

# Inicialização segura
app = initialize_app()

@https_fn.on_request()
def getItems(req):
    try:
        db = firestore.client()

        docs = db.collection("items").stream()
        data = []

        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }, 500