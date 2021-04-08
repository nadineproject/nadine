from django.apps import AppConfig


class NadineConfig(AppConfig):
    name = 'nadine'
    default_auto_field = AppConfig.default_auto_field

    def ready(self):
        # Load and connect signal recievers
        import nadine.signals
