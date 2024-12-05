# Aplicacion1/management/commands/eliminar_reservas.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from Aplicacion1.models import Reserva

class Command(BaseCommand):
    help = 'Elimina reservas vencidas'

    def add_arguments(self, parser):
        # Argumento de fecha de vencimiento
        parser.add_argument('--fecha-vencimiento', type=str, help='Fecha límite de vencimiento de las reservas (formato YYYY-MM-DD)', required=True)

    def handle(self, *args, **kwargs):
        fecha_vencimiento = kwargs['fecha-vencimiento']
        
        # Convierte la fecha de vencimiento en un objeto datetime, convirtiéndola a aware si es necesario
        try:
            fecha_vencimiento = timezone.make_aware(datetime.strptime(fecha_vencimiento, "%Y-%m-%d"))
        except ValueError:
            self.stdout.write(self.style.ERROR('Fecha de vencimiento no válida, asegúrese de usar el formato correcto (YYYY-MM-DD).'))
            return

        # Filtra las reservas vencidas (en este caso, aquellas anteriores a la fecha de vencimiento y no confirmadas)
        reservas_vencidas = Reserva.objects.filter(fecha_hora_inicio__lt=fecha_vencimiento, confirmada=False)

        # Elimina las reservas vencidas
        count, _ = reservas_vencidas.delete()

        # Muestra el resultado
        if count:
            self.stdout.write(self.style.SUCCESS(f'Se han eliminado {count} reservas vencidas.'))
        else:
            self.stdout.write(self.style.SUCCESS('No se encontraron reservas vencidas.'))
