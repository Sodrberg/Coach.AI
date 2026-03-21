"""Session authentication dependency for FastAPI routes."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Header, HTTPException, Query

from app.models.user import Session
from app.storage.json_store import store

logger = logging.getLogger(__name__)


async def get_authenticated_user(
    session_id: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
) -> Session:
    """
    FastAPI dependency that validates the user's session.

    Accepts session_id from query param (current frontend) or X-Session-Id
    header (future clients). Returns the Session object with verified user_id.
    """
    sid = session_id or x_session_id
    if not sid:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide session_id query param or X-Session-Id header.",
        )

    session = store.get_session(sid)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")

    # Check expiry if set (existing sessions without expires_at are allowed)
    if session.expires_at:
        try:
            expires = datetime.fromisoformat(session.expires_at)
            if datetime.now() > expires:
                logger.info(f"Session {sid} expired for user {session.user_id}")
                raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
        except ValueError:
            # Malformed expires_at — treat as valid to avoid locking out users
            logger.warning(f"Malformed expires_at for session {sid}: {session.expires_at}")

    return session


def validate_user_id_matches_session(body_user_id: str, session: Session) -> None:
    """
    Verify that a user_id in a request body matches the authenticated session.

    Raises 403 if they don't match — prevents user A from writing data for user B.
    """
    if body_user_id != session.user_id:
        logger.warning(
            f"User ID mismatch: body={body_user_id}, session={session.user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="User ID in request does not match authenticated session.",
        )
