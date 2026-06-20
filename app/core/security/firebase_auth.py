import json
import os

import firebase_admin
from firebase_admin import auth, credentials


def _get_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        service_account_json = os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"]
        service_account_info = json.loads(service_account_json)
        credential = credentials.Certificate(service_account_info)
        return firebase_admin.initialize_app(credential)


def verify_firebase_token(token: str) -> str | None:
    try:
        _get_firebase_app()
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        return uid if isinstance(uid, str) else None
    except Exception:
        return None
