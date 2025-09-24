from django.conf import settings

DEFAULT_LANG = settings.LANGUAGES[0][0]


def get_translated(obj, attr):
    key = f"{attr}_{DEFAULT_LANG}"
    val = getattr(obj, key, None)
    if not val:
        val = getattr(obj, attr)
    return val
