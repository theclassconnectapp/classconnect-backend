"""
Notification router — sends FCM push to group members when a message is sent.
Called by Flutter after writing a message to Firestore.
"""
import asyncio
import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from firebase_admin import firestore

from app.core.database.session import get_db
from app.core.security.firebase_auth import _get_firebase_app
from app.features.auth.presentation.dependencies import get_current_user
from app.features.auth.data.models.user_db import User
from app.shared.services.notification_bus import send_notification

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/notify", tags=["notifications"])


class MessageNotifyRequest(BaseModel):
    college_id: str
    group_id: str
    sender_name: str
    message_text: str


def _get_group_member_uids(college_id: str, group_id: str) -> list[str]:
    app = _get_firebase_app()
    db = firestore.client(app=app)
    group_ref = db.collection(f"colleges/{college_id}/groups").document(group_id)
    group = group_ref.get()
    if not group.exists:
        return []
    data = group.to_dict() or {}
    members = data.get("members", [])
    uids = []
    for m in members:
        if isinstance(m, dict):
            uid = m.get("uid") or m.get("id")
        else:
            uid = m
        if uid:
            uids.append(uid)
    return uids


@router.post("/message")
async def notify_message(
    req: MessageNotifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        uids = await asyncio.to_thread(
            _get_group_member_uids, req.college_id, req.group_id
        )
        # Remove sender from recipients
        uids = [uid for uid in uids if uid != current_user.uid]

        if not uids:
            return {"sent": 0}

        # Fetch FCM tokens from Postgres
        result = await db.execute(
            select(User.fcm_token).where(
                User.uid.in_(uids),
                User.fcm_token.isnot(None),
            )
        )
        tokens = [row[0] for row in result.fetchall()]

        # Send notifications
        for token in tokens:
            await send_notification(
                fcm_token=token,
                title=req.sender_name,
                body=req.message_text[:100],
                data={
                    "group_id": req.group_id,
                    "college_id": req.college_id,
                    "type": "new_message",
                },
            )

        logger.info("notifications_sent", group_id=req.group_id, count=len(tokens))
        return {"sent": len(tokens)}

    except Exception as e:
        logger.error("notify_failed", error=str(e))
        return {"sent": 0, "error": str(e)}
