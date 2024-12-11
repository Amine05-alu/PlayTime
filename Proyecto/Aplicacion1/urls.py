from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import index  # Asegúrate de importar la vista index
from .views import (
    InstalacionListView, 
    index, 
    InstalacionDetailView, 
    CampoListView, 
    CampoDetailView, 
    ReservaListView, 
    ReservaCreateView,
)

urlpatterns = [
    path("", index, name="index"),  # Ruta para la página principal
    path("instalaciones/", InstalacionListView.as_view(), name="instalacion_list"),
    path("instalaciones/<int:pk>/", InstalacionDetailView.as_view(), name="instalacion_detail"),
    path("campos/", CampoListView.as_view(), name="campo_list"),
    path("campos/<int:pk>/", CampoDetailView.as_view(), name="campo_detail"),
    path("reservas/", ReservaListView.as_view(), name="reserva_list"),
    path("reservas/nueva/", ReservaCreateView.as_view(), name="reserva_create"),
    path('reservar/', views.crear_reserva, name='crear_reserva'),
    path('get_campos/<int:instalacion_id>/', views.get_campos, name='get_campos'),
    path('login/', views.IniciarSesion.as_view(), name='login'),
    path('register/', views.RegistroUsuario.as_view(), name='register'),
    path('cerrar-sesion/', views.CerrarSesion.as_view(), name='cerrar_sesion'),
    path('ver-perfil/', views.ver_perfil, name='ver_perfil'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('eliminar-perfil/', views.eliminar_perfil, name='eliminar_perfil'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Aquí utilizas la vista de logout de Django
    path('home/', views.home, name='home'),  # Vista 'home' con el nombre 'home'
    path('mis-reservas/', views.lista_reservas, name='lista_reservas'),
    path('profile/', views.profile, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('buscar-instalaciones/', views.buscar_instalaciones, name='buscar_instalaciones'),
    path('instalaciones/', views.lista_instalaciones, name='lista_instalaciones'),
    path('instalaciones/<int:instalacion_id>/', views.detalle_instalacion, name='detalle_instalacion'),
    path('lista_instalaciones/', views.lista_instalaciones, name='lista_instalaciones'),
    path('lista_instalaciones/detalle_instalacion/<int:instalacion_id>/', views.detalle_instalacion, name='detalle_instalacion'),
    path('reservar_campo/<int:campo_id>/', views.reservar_campo, name='reservar_campo'),
    path('reservar_campo_confirmado/<int:campo_id>/', views.reservar_campo_confirmado, name='reservar_campo_confirmado'),
    path('reservar/<int:campo_id>/', views.reservar_campo, name='reservar_campo'),
    path('reservar_campo/<int:campo_id>/', views.reservar_campo, name='reservar_campo'),
    path('api/horarios_disponibles/<str:fecha>/', views.horarios_disponibles, name='horarios_disponibles'),
    path('api/horarios_por_campo/<int:campo_id>/<str:fecha>/', views.obtener_horarios_por_campo_y_fecha, name='obtener_horarios_por_campo_y_fecha'),
    path('api/horas_disponibles/<int:campo_id>/', views.obtener_horas_disponibles, name='obtener_horas_disponibles'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
