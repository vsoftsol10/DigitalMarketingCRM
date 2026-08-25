# from django.contrib.auth import authenticate
# from rest_framework.exceptions import AuthenticationFailed


# def login_user(email: str, password: str):
#     user = authenticate(
#         username=email,
#         password=password,
#     )

#     if not user:
#         raise AuthenticationFailed(
#             "Invalid email or password."
#         )

#     if not user.is_active:
#         raise AuthenticationFailed(
#             "Your account is inactive."
#         )

#     return user

from django.contrib.auth import authenticate

from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import User


def login_user(email: str, password: str):
    user = authenticate(
        username=email,
        password=password,
    )

    if not user:
        raise AuthenticationFailed(
            "Invalid email or password."
        )

    if user.is_deleted:
        raise AuthenticationFailed(
            "This account is no longer available."
        )

    if not user.is_active:
        raise AuthenticationFailed(
            "Your account is inactive."
        )

    return user


def change_user_password(
    user: User,
    new_password: str,
):
    user.set_password(new_password)

    user.save(
        update_fields=[
            "password",
            "updated_at",
        ]
    )

    return user