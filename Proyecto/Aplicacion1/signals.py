from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil

@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:  # Solo cuando el usuario es creado por primera vez
        if not Perfil.objects.filter(usuario=instance).exists():  # Verifica si ya existe el perfil
            Perfil.objects.create(usuario=instance)  # Crea el perfil solo si no existe
