from django.apps import AppConfig


class Aplicacion1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Aplicacion1'
    
    def ready(self):
        import Aplicacion1.signals  # Asegúrate de que este nombre sea correcto
