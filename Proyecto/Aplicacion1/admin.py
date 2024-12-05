from django.contrib import admin
from .models import Instalacion, Campo, Reserva, Perfil

# Registra tus modelos aquí
admin.site.register(Perfil)
admin.site.register(Instalacion)
admin.site.register(Campo)
admin.site.register(Reserva)
