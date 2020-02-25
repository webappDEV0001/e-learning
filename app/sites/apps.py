from django.apps import AppConfig


class SitesConfig(AppConfig):
    name = 'sites'
    label = "Uploading"
    verbose_name = "Uploading"

    def ready(self):
        import sites.signals