from django.contrib.auth.backends import ModelBackend
import re

from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        "token": token,
        "username": user.username,
        "user_id": user.id,
    }


def get_user_by_account(account):
    if re.match(r'^1[3-9]\d{9}$', account):
        user = User.objects.get(mobile=account)
    else:
        user = User.objects.get(username = account)

    return user


class UsernameMobileAuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)

        if user is not None and user.check_password(password):
            return user