from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from datetime import timedelta

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    edad = models.PositiveIntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f'{self.usuario.username} - Edad: {self.edad}, Teléfono: {self.telefono}'


# Modelo de Instalación
class Instalacion(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15)
    horario_apertura = models.TimeField()
    horario_cierre = models.TimeField()
    descripcion = models.TextField(blank=True, null=True)  # La descripción puede ser nula

    def __str__(self):
        return self.nombre

# Modelo de Campo (cancha) asociado a Instalación
class Campo(models.Model):
    nombre = models.CharField(max_length=50)
    tipo_campo = models.CharField(max_length=50)
    capacidad_jugadores = models.IntegerField()
    disponible = models.BooleanField(default=True)
    instalacion = models.ForeignKey(Instalacion, on_delete=models.CASCADE, related_name='canchas')
    deporte = models.CharField(max_length=50, default='futbol')  # Valor por defecto "futbol"

    def __str__(self):
        return f'{self.nombre} - {self.instalacion.nombre} ({self.deporte})'

# Modelo de Reserva asociado a Campo y Usuario
# Aplicacion1/models.py

class Reserva(models.Model):
    cancha = models.ForeignKey(Campo, on_delete=models.CASCADE, related_name='reservas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    fecha_hora_inicio = models.DateTimeField()
    duracion = models.IntegerField(default=1)  # Duración en horas
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    confirmada = models.BooleanField(default=False)  # Agregar campo confirmada
    foto_instalacion = models.ImageField(upload_to="reservas/fotos_instalacion", blank=True, null=True)  # Foto de la instalación
    archivo_reserva = models.FileField(upload_to="reservas/documentos", blank=True, null=True)  # Documento adjunto
    comentario = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['-fecha_hora_inicio']),  # Índice para ordenar por fecha
        ]
    def __str__(self):
        return f'Reserva de {self.usuario.username} en {self.cancha.nombre} el {self.fecha_hora_inicio}'
    
    def clean(self):
        if self.cancha.disponible is False:
            raise ValidationError('La cancha no está disponible en este horario.')

    def save(self, *args, **kwargs):
        self.full_clean()  # Llama a clean antes de guardar
        super().save(*args, **kwargs)

    def clean(self):
        # Validar conflictos de horarios
        reservas_conflictivas = Reserva.objects.filter(
            cancha=self.cancha,
            fecha_hora_inicio__lt=self.fecha_hora_inicio + timedelta(hours=1),
            fecha_hora_inicio__gte=self.fecha_hora_inicio,
        ).exclude(id=self.id)

        if reservas_conflictivas.exists():
            raise ValidationError('Ya existe una reserva en este horario para la cancha seleccionada.')

@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
