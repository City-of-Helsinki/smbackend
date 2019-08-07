from django.core.exceptions import FieldDoesNotExist


def check_valid_concrete_field(model, f):
    try:
        return model._meta.get_field(f).concrete
    except FieldDoesNotExist:
        return False
    return False
