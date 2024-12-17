from django import forms
from .models import Reserva, Campo, Perfil, Instalacion
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Formulario de contacto
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

    def send_email(self):
        # Lógica para enviar el correo utilizando self.cleaned_data
        pass

# Formulario de reserva
class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cancha', 'instalacion', 'fecha_hora_inicio', 'duracion', 'foto_instalacion', 'archivo_reserva', 'comentario']

    # Campo para seleccionar la instalación
    instalacion = forms.ModelChoiceField(
        queryset=Instalacion.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Instalación"
    )

    # Campo para seleccionar la cancha
    cancha = forms.ModelChoiceField(
        queryset=Campo.objects.none(),  # Inicialmente no se muestran canchas
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cancha"
    )

    # Campo para seleccionar la hora de inicio
    fecha_hora_inicio = forms.ChoiceField(
        choices=[],  # Se llenará dinámicamente con las horas disponibles
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Hora de inicio"
    )

    # Duración
    duracion = forms.IntegerField(
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Duración (horas)"
    )

    # Filtrar las canchas disponibles según la instalación seleccionada
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instalacion' in self.data:
            try:
                instalacion_id = int(self.data.get('instalacion'))
                self.fields['cancha'].queryset = Campo.objects.filter(instalacion_id=instalacion_id)
            except (ValueError, TypeError):
                pass  # Si no se ha seleccionado una instalación aún, no hacemos nada
        elif self.instance.pk:
            self.fields['cancha'].queryset = self.instance.instalacion.canchas.all()

        # Actualiza las horas disponibles según el campo seleccionado
        if 'cancha' in self.data:
            campo_id = self.data.get('cancha')
            self.fields['fecha_hora_inicio'].choices = self.obtener_horas_disponibles(campo_id)

    def obtener_horas_disponibles(self, campo_id):
        # Obtén las horas disponibles para el campo seleccionado
        campo = Campo.objects.get(id=campo_id)
        horas_ocupadas = Reserva.objects.filter(cancha=campo, fecha_hora_inicio__gte=timezone.now()).values_list('fecha_hora_inicio', flat=True)
        
        horas_disponibles = []
        for i in range(24):
            hora = str(i).zfill(2) + ":00"
            if hora not in horas_ocupadas:
                horas_disponibles.append((hora, hora))

        return horas_disponibles


# Formulario de perfil
class PerfilForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Nombre de Usuario')

    class Meta:
        model = Perfil
        fields = []  # No incluyas 'username' aquí

    def __init__(self, *args, **kwargs):
        super(PerfilForm, self).__init__(*args, **kwargs)
        self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        perfil = super(PerfilForm, self).save(commit=False)
        perfil.user.username = self.cleaned_data['username']
        if commit:
            perfil.user.save()
            perfil.save()
        return perfil

# Formulario de creación de usuario personalizado
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class BusquedaInstalacionesForm(forms.Form):
    TIPO_DEPORTE_CHOICES = [
        ('', 'Selecciona un deporte'),
        ('futbol', 'Fútbol'),
        ('tenis', 'Tenis'),
        ('baloncesto', 'Baloncesto'),
        # Añadir más deportes si es necesario
    ]
    deporte = forms.ChoiceField(choices=TIPO_DEPORTE_CHOICES, required=False)

class ModificarReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cancha', 'fecha_hora_inicio']
        widgets = {
            'fecha_hora_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'cancha': 'Cancha',
            'fecha_hora_inicio': 'Fecha y Hora',
        }
