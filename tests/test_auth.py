from unittest.mock import patch
import handlers.auth as auth


def test_authorized_user():
    with patch.object(auth, "AUTHORIZED_USER_IDS", [123, 456]):
        assert auth.is_authorized(123) is True
        assert auth.is_authorized(456) is True


def test_unauthorized_user():
    with patch.object(auth, "AUTHORIZED_USER_IDS", [123]):
        assert auth.is_authorized(999) is False
        assert auth.is_authorized(0) is False


def test_empty_authorized_list():
    with patch.object(auth, "AUTHORIZED_USER_IDS", []):
        assert auth.is_authorized(123) is False
