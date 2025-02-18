from django.apps import AppConfig


class OyeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "oye"

    def ready(self):
        import oye.signals