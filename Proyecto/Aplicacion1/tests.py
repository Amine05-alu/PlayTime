# Aplicacion1/tests.py

from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth.models import User  # Asegúrate de importar User
from Aplicacion1.models import Reserva, Campo, Instalacion
from django.utils import timezone

class ComandoEliminarReservasTest(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.usuario1 = User.objects.create_user(username='usuario1', password='password1')
        self.usuario2 = User.objects.create_user(username='usuario2', password='password2')

        # Crear una instalación y un campo asociado
        self.instalacion = Instalacion.objects.create(
            nombre='Instalación A',
            direccion='Calle Ficticia 123',
            telefono='123456789',
            horario_apertura='08:00:00',
            horario_cierre='18:00:00'
        )
        self.campo = Campo.objects.create(
            nombre='Campo 1',
            tipo_campo='Futbol',
            capacidad_jugadores=10,
            instalacion=self.instalacion
        )

    def test_eliminar_reservas_vencidas(self):
        # Crear una reserva vencida y no confirmada
        reserva_vencida = Reserva.objects.create(
            usuario=self.usuario1,  # Usar el usuario creado
            cancha=self.campo,
            fecha_hora_inicio=timezone.datetime(2024, 11, 6, 12, 0),  # Fecha vencida
            confirmada=False,  # No confirmada
            duracion=2,
            precio=50.00
        )
        
        # Llamar al comando
        call_command('eliminar_reservas', '--fecha-vencimiento=2024-11-07')
        
        # Verificar que la reserva fue eliminada
        self.assertEqual(Reserva.objects.count(), 0)

    def test_no_eliminar_reservas_confirmadas(self):
        # Crear una reserva confirmada (no debe eliminarse)
        reserva_confirmada = Reserva.objects.create(
            usuario=self.usuario2,  # Usar el usuario creado
            cancha=self.campo,
            fecha_hora_inicio=timezone.datetime(2024, 11, 6, 12, 0),  # Fecha vencida
            confirmada=True,  # Confirmada
            duracion=2,
            precio=50.00
        )
        
        # Llamar al comando
        call_command('eliminar_reservas', '--fecha-vencimiento=2024-11-07')
        
        # Verificar que la reserva confirmada no ha sido eliminada
        self.assertEqual(Reserva.objects.count(), 1)  # Debería quedar una reserva confirmada
