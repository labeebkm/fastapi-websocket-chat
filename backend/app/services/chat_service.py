from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models import User, Message


def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )


def save_message(
    db: Session,
    sender_username: str,
    receiver_username: str,
    content: str,
) -> Message:
    sender = get_user_by_username(db, sender_username)
    receiver = get_user_by_username(db, receiver_username)

    if sender is None:
        raise ValueError(
            f"Sender '{sender_username}' does not exist"
        )

    if receiver is None:
        raise ValueError(
            f"Receiver '{receiver_username}' does not exist"
        )

    message = Message(
        sender_id=sender.id,
        receiver_id=receiver.id,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_message_history(
    db: Session,
    user_a: str,
    user_b: str,
    before_id: int | None = None,
    limit: int = 4,
) -> tuple[list[Message], bool]:
    """
    Returns (messages, has_more).
    messages are the most recent `limit` messages older than `before_id`
    (or the most recent `limit` overall if before_id is None),
    returned in chronological order.
    """
    a = get_user_by_username(db, user_a)
    b = get_user_by_username(db, user_b)

    if a is None or b is None:
        return [], False

    # Cap window size so a client can't request an unbounded history.
    limit = max(1, min(limit, 100))

    query = db.query(Message).filter(
        or_(
            and_(
                Message.sender_id == a.id,
                Message.receiver_id == b.id,
            ),
            and_(
                Message.sender_id == b.id,
                Message.receiver_id == a.id,
            ),
        )
    )

    if before_id is not None:
        query = query.filter(Message.id < before_id)

    # Fetch newest-first so LIMIT gives us the most recent window,
    # then reverse for chronological display order.
    rows = (
        query
        .order_by(Message.id.desc())
        .limit(limit + 1)   # fetch one extra to detect if more remain
        .all()
    )

    has_more = len(rows) > limit
    rows = rows[:limit]
    rows.reverse()

    return rows, has_more