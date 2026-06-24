"""
NotificationBus — FCM HTTP v1 API implementation.
FastAPI backend sends to FCM → device.
"""
import json
import httpx
import structlog
from google.oauth2 import service_account
from google.auth.transport.requests import Request

logger = structlog.get_logger()

PROJECT_ID = "the-classconnect"
FCM_ENDPOINT = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


def _get_access_token() -> str:
    import os
    import json
    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        service_account_info = json.loads(service_account_json)
        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )
    else:
        # fallback for local dev
        creds = service_account.Credentials.from_service_account_file(
            "firebase-service-account.json",
            scopes=SCOPES,
        )
    creds.refresh(Request())
    return creds.token


async def send_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: dict = {},
) -> None:
    try:
        access_token = _get_access_token()
        payload = {
            "message": {
                "token": fcm_token,
                "notification": {"title": title, "body": body},
                "data": {k: str(v) for k, v in data.items()},
                "android": {
                    "priority": "high",
                },
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FCM_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if response.status_code == 200:
                logger.info("fcm_sent", token_prefix=fcm_token[:20], title=title)
            else:
                logger.error("fcm_failed", status=response.status_code, body=response.text)
    except Exception as e:
        logger.error("fcm_error", error=str(e))
