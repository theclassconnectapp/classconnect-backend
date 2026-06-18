"""
NotificationBus — Phase 1: FCM token storage only.
Phase 2 will add send_to_user() and send_to_group() here,
replacing the Firebase Cloud Functions notification triggers.

FCM delivery is unavoidable on Android/iOS.
Your FastAPI backend sends to FCM HTTP v1 API → FCM → device.
Same as Instagram, WhatsApp, Telegram.
"""
import httpx
import structlog

logger = structlog.get_logger()

FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"


async def send_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: dict = {},
) -> None:
    """
    Phase 2 implementation — send push via FCM HTTP v1 API.
    Requires: FCM service account key → OAuth2 bearer token.
    """
    # TODO Phase 2: implement with google-auth service account credentials
    logger.info("fcm_send_placeholder", token_prefix=fcm_token[:20], title=title)
