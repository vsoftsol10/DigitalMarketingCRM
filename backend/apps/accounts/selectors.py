from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_by_email(email: str):
    return User.objects.filter(
        email=email,
        is_active=True,
        is_deleted=False,
    ).first()


def get_user_by_id(user_id):
    return User.objects.filter(
        id=user_id,
        is_active=True,
        is_deleted=False,
    ).first()