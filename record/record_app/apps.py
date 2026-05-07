from django.apps import AppConfig


class RecordAppConfig(AppConfig):
    name = "record_app"
    
    def ready(self):
        import record_app.signals
