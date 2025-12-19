from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        import os
        """Django App initialization"""
        if os.environ.get('RUN_MAIN') == 'true':
            # Solo ejecutar en el proceso principal (no en el reloader)
            from .docker_utils import start_monitoring_thread
            start_monitoring_thread()
