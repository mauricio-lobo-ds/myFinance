from config import AUTHORIZED_USER_IDS


def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USER_IDS
