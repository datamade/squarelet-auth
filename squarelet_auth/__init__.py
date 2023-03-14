# Django
from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured

# SquareletAuth
from squarelet_auth import settings


def model_from_setting(setting_key):
    setting_value = getattr(settings, setting_key)
    try:
        return django_apps.get_model(setting_value, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            f"SQUARELET_{setting_key} must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"SQUARELET_{setting_key} refers to model "
            f"'{setting_value}' that has not been installed"
        )
