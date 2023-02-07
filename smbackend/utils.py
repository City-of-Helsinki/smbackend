import traceback
from functools import wraps

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail


def get_emails_to_notify():
    """
    Return email addresses for users in group 'settings.CELERY_ADMIN_GROUP'.
    """
    return [
        user.email
        for user in User.objects.filter(groups__name=settings.CELERY_ADMIN_GROUP)
    ]


def shared_task_email(func):
    """
    Replacement for @shared_task decorator that emails users in group settins.CELERY_ADMIN_GROUP
     if an exception is raised.
    """

    @wraps(func)
    def new_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            notify_emails = get_emails_to_notify()
            if len(notify_emails) > 0:
                subject = "Celery task failure"
                message = f"Function: {str(func)} \n"
                message += traceback.format_exc()
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    notify_emails,
                    fail_silently=False,
                )
            raise

    return shared_task(new_func)
