import os
import json
import logging

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlmodel import Session, select, and_
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from pywebpush import webpush, WebPushException
from core.database import get_session
from middleware import verify_user
from models import Subscription

router = APIRouter()
security = HTTPBearer()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VAPID_PRIVATE_KEY = os.getenv("NEXT_PUBLIC_VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("NEXT_PUBLIC_VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {"sub": "mailto:example@mail.com"}

subscriptions = []


@router.post("/subscribe")
async def subscribe(
    request: Request,
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)
    subscription = await request.json()
    endpoint = subscription.get("endpoint")
    keys = json.dumps(subscription.get("keys"))
    # current subscription
    curr_subcription = session.exec(
        select(Subscription).where(
            and_(
                Subscription.user_id == user.id,
                Subscription.endpoint == endpoint,
            )
        )
    ).first()
    if curr_subcription:
        curr_subcription.endpoint = endpoint
        curr_subcription.keys = keys
    else:
        # save subscription
        new_subscription = Subscription(
            endpoint=endpoint,
            keys=keys,
            user_id=user.id,
        )
        session.add(new_subscription)
    session.commit()
    session.flush()
    return {"message": "Subscription received"}


# TODO :: Delete this endpoint later (for test only)
@router.post("/send_notification")
async def send_notification(session: Session = Depends(get_session)):
    subscriptions = session.exec(select(Subscription)).all()
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": json.loads(subscription.keys),
                },
                data=json.dumps(
                    {
                        "title": "New Notification",
                        "body": "This is a test notification",
                    }
                ),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
        except WebPushException as e:
            # Detect if the subscription is invalid or expired
            if e.response and e.response.status_code in {404, 410}:
                logger.info(
                    "Removing invalid subscription:", subscription.endpoint
                )
                # Remove the invalid subscription from the database
                session.delete(subscription)
                session.commit()
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Subscription failed.",
            )
    return {"message": "Notifications sent"}
