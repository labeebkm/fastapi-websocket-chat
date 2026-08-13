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