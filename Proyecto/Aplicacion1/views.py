from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time, timedelta
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import make_aware
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework import serializers
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from .forms import ModificarReservaForm
from django.core.exceptions import ValidationError

from .models import Instalacion, Campo, Reserva, Perfil
from .forms import ReservaForm, CustomUserCreationForm, PerfilForm, BusquedaInstalacionesForm


def info_instalacion(request, id):
    instalacion = get_object_or_404(Instalacion, id=id)
    return render(request, 'info_instalacion.html', {'instalacion': instalacion})

def disponible_instalaciones(request):
    instalaciones = Instalacion.objects.all()
    return render(request, 'disponible_instalaciones.html', {'instalaciones': instalaciones})

def modificar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if request.method == 'POST':
        form = ModificarReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            messages.success(request, 'La reserva ha sido modificada con éxito.')
            return redirect('mis_reservas')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = ModificarReservaForm(instance=reserva)

    return render(request, 'modificar_reserva.html', {'form': form, 'reserva': reserva})

def mis_reservas(request):
    if request.method == 'POST' and 'cancelar_reserva' in request.POST:
        reserva_id = request.POST.get('reserva_id')
        try:
            reserva = Reserva.objects.get(id=reserva_id, usuario=request.user)
            reserva.delete()
            messages.success(request, 'La reserva ha sido cancelada con éxito.')
        except Reserva.DoesNotExist:
            messages.error(request, 'No se pudo encontrar la reserva.')

    reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_hora_inicio')
    return render(request, 'mis_reservas.html', {'reservas': reservas})

class CampoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campo
        fields = '__all__'  # Esto serializa todos los campos del modelo. Puedes especificar los campos si prefieres.

class HorariosDisponiblesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campo.objects.all()  # Esto proporciona el queryset que espera DRF
    serializer_class = CampoSerializer  # Asegúrate de tener un serializador de Campo si deseas usar este enfoque

# ===========================
# Vista para obtener horarios disponibles (APIView)
# ===========================
class HorariosDisponiblesAPIView(APIView):
    permission_classes = [AllowAny]  # Desactiva la validación de permisos
    
    def get(self, request, fecha):
        try:
            # Convertir la fecha desde el formato esperado
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use AAAA-MM-DD."}, status=400)

        campos = Campo.objects.all()
        resultado = []

        for campo in campos:
            horarios = [
                {
                    'hora': f'{hora}:00',
                    'disponible': not Reserva.objects.filter(
                        cancha=campo,
                        fecha_hora_inicio=make_aware(datetime.combine(fecha_dt, time(hora)))
                    ).exists()
                }
                for hora in range(8, 23)
            ]

            resultado.append({
                'id': campo.id,
                'nombre': campo.nombre,
                'tipo_campo': campo.tipo_campo,
                'capacidad_jugadores': campo.capacidad_jugadores,
                'horarios': horarios
            })

        return Response({'campos': resultado})


# ===========================
# Vista para obtener horarios disponibles (función basada en vista)
# ===========================
@api_view(['GET'])
def horarios_disponibles(request, fecha):
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use AAAA-MM-DD."}, status=400)

    campos = Campo.objects.all()
    resultado = []

    for campo in campos:
        horarios = [
            {
                'hora': f'{hora}:00',
                'disponible': not Reserva.objects.filter(
                    cancha=campo,
                    fecha_hora_inicio=make_aware(datetime.combine(fecha_dt, time(hora)))
                ).exists()
            }
            for hora in range(8, 23)
        ]

        resultado.append({
            'id': campo.id,
            'nombre': campo.nombre,
            'tipo_campo': campo.tipo_campo,
            'capacidad_jugadores': campo.capacidad_jugadores,
            'horarios': horarios
        })

    return Response({'campos': resultado})


# ===========================
# Vista para obtener horarios disponibles por campo y fecha
# ===========================
@api_view(['GET'])
def obtener_horarios_por_campo_y_fecha(request, campo_id, fecha):
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        campo = get_object_or_404(Campo, id=campo_id)

        horarios_disponibles = [
            datetime.combine(fecha_dt, time(hour)) for hour in range(8, 23)
        ]

        reservas_existentes = Reserva.objects.filter(
            cancha=campo,
            fecha_hora_inicio__date=fecha_dt
        ).values_list('fecha_hora_inicio', flat=True)

        horarios_libres = [
            horario for horario in horarios_disponibles if horario not in reservas_existentes
        ]

        return Response({
            "campo_id": campo.id,
            "nombre": campo.nombre,
            "tipo_campo": campo.tipo_campo,
            "capacidad_jugadores": campo.capacidad_jugadores,
            "horarios": [
                {
                    "hora": horario.strftime("%H:%M"),
                    "disponible": horario in horarios_libres
                }
                for horario in horarios_disponibles
            ]
        })

    except Campo.DoesNotExist:
        return Response({"error": "El campo especificado no existe."}, status=404)
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use AAAA-MM-DD."}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ===========================
# Vista para obtener horas disponibles por campo
# ===========================
@api_view(['GET'])
def obtener_horas_disponibles(request, campo_id):
    campo = get_object_or_404(Campo, id=campo_id)
    today = timezone.now().date()  # Asegurarse de que se obtiene el día actual
    horarios_disponibles = [today + timedelta(hours=hour) for hour in range(8, 23)]

    # Filtrar horas ya reservadas
    horas_reservadas = set(
        Reserva.objects.filter(cancha=campo, fecha_hora_inicio__date=today)
        .values_list('fecha_hora_inicio', flat=True)
    )

    # Filtrar las horas libres
    horas_libres = [hora for hora in horarios_disponibles if hora not in horas_reservadas]

    # Devolver las horas disponibles
    return JsonResponse({'horas_disponibles': [hora.strftime("%H:%M") for hora in horas_libres]})

def reservar_campo_confirmado(request, campo_id):
    campo = Campo.objects.get(id=campo_id)
    today = timezone.now().date()

    # Obtener los horarios disponibles
    horarios_disponibles = [today + timedelta(hours=hour) for hour in range(8, 23)]

    # Obtener las horas reservadas para el campo
    horas_reservadas = set(
        Reserva.objects.filter(cancha=campo, fecha_hora_inicio__date=today)
        .values_list('fecha_hora_inicio', flat=True)
    )

    hora_reserva = None  # Inicializamos la variable
    comentarios = request.POST.get('comentarios', "No hay comentarios.")  # Comentario por defecto

    if request.method == 'POST':
        hora_reserva_str = request.POST.get('hora_reserva', None)

        if not hora_reserva_str:
            messages.error(request, "Debe seleccionar una hora para reservar.")
            return redirect('reservar_campo_confirmado', campo_id=campo.id)

        # Convertir la hora seleccionada a un objeto datetime
        try:
            hora_reserva = datetime.strptime(hora_reserva_str, "%H:%M").replace(
                year=today.year, month=today.month, day=today.day
            )
        except ValueError:
            messages.error(request, "Formato de hora inválido.")
            return redirect('reservar_campo_confirmado', campo_id=campo.id)

        if hora_reserva in horas_reservadas:
            messages.error(request, "La hora seleccionada ya está reservada. Por favor, elige otro horario.")
        else:
            try:
                Reserva.objects.create(
                    cancha=campo,
                    comentario=comentarios,
                    usuario=request.user,
                    fecha_hora_inicio=hora_reserva,
                    duracion=1,  # Duración de la reserva, ajusta según tu lógica
                    precio=20.00  # Precio o cualquier otro campo que necesites
                )
                messages.success(request, "Tu reserva ha sido realizada exitosamente.")
            except ValidationError as e:
                messages.error(request, "Error al crear la reserva: {}".format(e))

    # Mostrar la última reserva realizada por el usuario si existe
    reserva_reciente = Reserva.objects.filter(cancha=campo, usuario=request.user).order_by('-fecha_hora_inicio').first()
    if reserva_reciente:
        hora_reserva = reserva_reciente.fecha_hora_inicio
        comentarios = reserva_reciente.comentario or "No hay comentarios."

    return render(request, 'reservar_campo_confirmado.html', {
        'campo': campo,
        'horarios_disponibles': horarios_disponibles,
        'horas_reservadas': horas_reservadas,
        'hora_reserva': hora_reserva,
        'comentarios': comentarios,
        'mensaje': {
            'tipo': 'info',
            'titulo': 'Detalles de tu Reserva',
            'descripcion': 'Aquí están los detalles de tu reserva.'
        }
    })

def reservar_campo(request, campo_id):
    campo = get_object_or_404(Campo, id=campo_id)
    today = now().date()  # Obtenemos solo la fecha actual

    # Verificamos si hay un parámetro de fecha en la solicitud GET
    dia_reserva_str = request.GET.get('fecha')
    dia_reserva = parse_date(dia_reserva_str) if dia_reserva_str else today  # Si no hay fecha, usamos la de hoy

    # Generar los horarios disponibles para el día seleccionado
    horarios_disponibles = [
        datetime.combine(dia_reserva, datetime.min.time()) + timedelta(hours=hour)
        for hour in range(8, 23)
    ]

    # Filtrar las horas ya reservadas
    horas_reservadas = set(
        Reserva.objects.filter(
            cancha=campo,
            fecha_hora_inicio__date=dia_reserva
        ).values_list('fecha_hora_inicio', flat=True)
    )

    # Verificar si el formulario ha sido enviado
    if request.method == 'POST':
        hora_reserva_str = request.POST.get('hora_reserva')
        hora_reserva = datetime.strptime(hora_reserva_str, "%H:%M").replace(
            year=dia_reserva.year, month=dia_reserva.month, day=dia_reserva.day
        )

        # Verificar si la hora ya está reservada
        if hora_reserva in horas_reservadas:
            messages.error(request, "Este horario ya está reservado. Por favor elige otro.")
            return redirect('reservar_campo', campo_id=campo.id)

        # Crear la reserva
        reserva = Reserva.objects.create(
            cancha=campo,
            usuario=request.user,
            fecha_hora_inicio=hora_reserva,
            duracion=1,  # Asumiendo que es 1 hora
            precio=100.00  # Ajusta el precio según tu lógica
        )

        # Actualizar la disponibilidad del campo
        campo.disponible = False
        campo.save()

        messages.success(request, "Reserva realizada con éxito.")
        return redirect('mis_reservas')  # Redirige a la página de reservas del usuario

    # Pasar la información de los horarios disponibles y reservados al template
    return render(request, 'reservar_campo.html', {
        'campo': campo,
        'dia_reserva': dia_reserva,
        'horarios_disponibles': horarios_disponibles,
        'horas_reservadas': horas_reservadas,
    })

def lista_instalaciones(request):
    instalaciones = Instalacion.objects.all()
    return render(request, 'lista_instalaciones.html', {'instalaciones': instalaciones})

# Vista para los detalles de la instalación, con la lógica de reservar un horario
def detalle_instalacion(request, instalacion_id):
    try:
        instalacion = Instalacion.objects.get(id=instalacion_id)
    except Instalacion.DoesNotExist:
        return render(request, '404.html')

    # Obtener los campos disponibles de la instalación
    campos = instalacion.canchas.filter(disponible=True)

    # Definir el rango de horarios del día (por ejemplo de 8 AM a 10 PM)
    horarios_disponibles = [datetime.strptime(f'{hour}:00', '%H:%M') for hour in range(8, 23)]

    # Preparar un diccionario de reservas para cada campo
    reservas_por_campo = {}
    for campo in campos:
        reservas_por_campo[campo.id] = {}
        for hora in horarios_disponibles:
            reserva = Reserva.objects.filter(
                cancha=campo, 
                fecha_hora_inicio__hour=hora.hour,
                fecha_hora_inicio__minute=hora.minute
            ).first()

            if reserva:
                reservas_por_campo[campo.id][hora] = 'reservado'
            else:
                reservas_por_campo[campo.id][hora] = 'disponible'

    # Si el usuario hace una reserva, procesar la solicitud
    if request.method == 'POST':
        cancha_id = request.POST.get('cancha_id')
        hora_reserva = request.POST.get('hora_reserva')
        hora_reserva = datetime.strptime(hora_reserva, "%H:%M").replace(year=timezone.now().year, month=timezone.now().month, day=timezone.now().day)

        cancha = Campo.objects.get(id=cancha_id)
        
        # Verificar si el horario está disponible
        if Reserva.objects.filter(cancha=cancha, fecha_hora_inicio=hora_reserva).exists():
            messages.error(request, "Este horario ya está reservado.")
        else:
            reserva = Reserva.objects.create(
                cancha=cancha,
                usuario=request.user,
                fecha_hora_inicio=hora_reserva,
                duracion=1,  # Suponiendo que la reserva es por 1 hora
                precio=100.00  # Precio fijo (puede variar dependiendo de tu lógica)
            )
            # Marcar el campo como no disponible después de hacer la reserva
            cancha.disponible = False
            cancha.save()
            messages.success(request, "Reserva realizada con éxito.")

        return redirect('detalle_instalacion', instalacion_id=instalacion_id)

    # Pasar la instalación, los campos y las reservas al template
    context = {
        'instalacion': instalacion,
        'campos': campos,
        'horarios_disponibles': horarios_disponibles,
        'reservas_por_campo': reservas_por_campo,
    }

    return render(request, 'detalle_instalacion.html', context)

def buscar_instalaciones(request):
    form = BusquedaInstalacionesForm(request.GET)
    instalaciones = Instalacion.objects.all()  # Obtiene todas las instalaciones por defecto
    
    if form.is_valid():
        deporte = form.cleaned_data['deporte']
        if deporte:
            instalaciones = instalaciones.filter(tipo_de_deporte=deporte)  # Filtra por deporte
    
    return render(request, 'buscar_instalaciones.html', {
        'form': form,
        'instalaciones': instalaciones,
    })

def hacer_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST, request.FILES)
        if form.is_valid():
            # Si el formulario es válido, lo guardamos
            form.save()
            return redirect('reservas:lista_reservas')  # Redirigir a la lista de reservas
    else:
        form = ReservaForm()

    return render(request, 'reservas/hacer_reserva.html', {'form': form})

def profile(request):
    return render(request, 'profile.html')

def lista_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, 'lista_reservas.html', {'reservas': reservas})

# Vista principal (página de inicio)
def home(request):
    return render(request, 'home.html')  # O la plantilla que prefieras

# Vista para iniciar sesión
class IniciarSesion(LoginView):
    template_name = 'login.html'  # Ruta cambiada
    form_class = AuthenticationForm
    success_url = reverse_lazy('home')  # Redirige a la página de inicio tras iniciar sesión correctamente

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)

# Vista para registrarse
class RegistroUsuario(FormView):
    template_name = 'register.html'  # Ruta cambiada
    form_class = CustomUserCreationForm  # Usa tu formulario personalizado
    success_url = reverse_lazy('login')  # Redirige al login tras el registro exitoso

    def form_valid(self, form):
        user = form.save()  # Guarda el nuevo usuario
        login(self.request, user)  # Inicia sesión automáticamente después del registro (opcional)
        return super().form_valid(form)

# Vista para eliminar el perfil del usuario
@login_required
def eliminar_perfil(request):
    perfil = get_object_or_404(Perfil, user=request.user)

    if request.method == 'POST':
        perfil.delete()  # Elimina el perfil
        request.user.delete()  # Elimina el usuario
        messages.success(request, 'Tu cuenta ha sido eliminada con éxito.')
        return redirect('home')  # Redirige a la página de inicio o a donde desees

    return render(request, 'eliminar_perfil.html', {'perfil': perfil})

# Vista para cerrar sesión
class CerrarSesion(LogoutView):
    next_page = 'home'  # Redirige a la página de inicio tras cerrar sesión

# Vista para editar el perfil del usuario
@login_required
def editar_perfil(request):
    perfil = get_object_or_404(Perfil, usuario=request.user)
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('ver_perfil')  # Cambia la redirección si es necesario
    else:
        form = PerfilForm(instance=perfil)
    
    return render(request, 'editar_perfil.html', {'form': form})

# Vista para ver el perfil del usuario
@login_required
def ver_perfil(request):
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)  # Cambié 'user' por 'usuario'
    return render(request, 'ver_perfil.html', {'perfil': perfil})

# Vista principal (Índice)
def index(request):
    reservas = []
    resultados = None
    buscar_deporte = request.GET.get('buscar_deporte', '').strip()

    if request.user.is_authenticated:
        # Filtrar las reservas para el usuario autenticado
        reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_hora_inicio')  # Opcionalmente, ordenarlas

        # Cancelar la reserva si la solicitud es POST
        if request.method == 'POST' and 'cancelar_reserva' in request.POST:
            reserva_id = request.POST.get('reserva_id')
            try:
                reserva = Reserva.objects.get(id=reserva_id, usuario=request.user)
                reserva.delete()
                messages.success(request, 'Reserva cancelada exitosamente.')
            except Reserva.DoesNotExist:
                messages.error(request, 'Reserva no encontrada o no es tuya.')

    # Filtrar instalaciones o campos según el deporte buscado
    if buscar_deporte:
        resultados = Campo.objects.filter(deporte__icontains=buscar_deporte)

    return render(request, 'index.html', {
        'reservas': reservas,
        'resultados': resultados,
        'buscar_deporte': buscar_deporte,
    })

# Vista para crear una reserva
@login_required
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.usuario = request.user  # Asigna el usuario autenticado
            form.save()
            return redirect('reserva_exitosa')  # Redirige a una página de éxito
    else:
        form = ReservaForm()
    
    # Aquí agregamos las instalaciones a la plantilla
    instalaciones = Instalacion.objects.all()  # Obtenemos todas las instalaciones

    return render(request, 'crear_reserva.html', {'form': form, 'instalaciones': instalaciones})

# Vista para obtener los campos disponibles según la instalación seleccionada
def get_campos(request, instalacion_id):
    try:
        instalacion = Instalacion.objects.get(id=instalacion_id)
        campos = Campo.objects.filter(instalacion=instalacion).values('id', 'nombre')
        return JsonResponse({'campos': list(campos)})
    except Instalacion.DoesNotExist:
        return JsonResponse({'campos': []}, status=404)

# Listado de instalaciones
class InstalacionListView(ListView):
    model = Instalacion
    context_object_name = "instalaciones"
    template_name = "instalacion_list.html"

# Detalles de una instalación
class InstalacionDetailView(DetailView):
    model = Instalacion
    context_object_name = "instalacion"
    template_name = "instalacion_detail.html"

# Listado de campos
class CampoListView(ListView):
    model = Campo
    context_object_name = "campos"  # Cambiado a campos
    template_name = "campo_list.html"

# Detalles de un campo
class CampoDetailView(DetailView):
    model = Campo
    context_object_name = "campo"
    template_name = "campo_detail.html"

# Listado de reservas del usuario
class ReservaListView(LoginRequiredMixin, ListView):
    model = Reserva
    context_object_name = "reservas"
    template_name = "reserva_list.html"

    def get_queryset(self):
        # Filtrar reservas por el usuario actual
        return Reserva.objects.filter(usuario=self.request.user)

# Formulario para crear una nueva reserva
class ReservaCreateView(LoginRequiredMixin, FormView):
    # (código existente)

    def form_valid(self, form):
        reserva = form.save(commit=False)
        reserva.usuario = self.request.user
        
        # Validación de conflictos de horarios
        conflictos = Reserva.objects.filter(
            cancha=reserva.cancha,
            fecha_hora_inicio__lt=reserva.fecha_hora_inicio + timezone.timedelta(hours=reserva.duracion),
            fecha_hora_inicio__gte=reserva.fecha_hora_inicio
        ).exists()

        if conflictos:
            form.add_error('fecha_hora_inicio', 'Este horario ya está reservado. Por favor elige otro.')
            return self.form_invalid(form)

        reserva.save()  # Guarda la reserva si no hay conflictos
        return super().form_valid(form)