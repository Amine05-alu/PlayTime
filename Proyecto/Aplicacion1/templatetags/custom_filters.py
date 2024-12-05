# Aplicacion1/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def get_item(value, arg):
    """Devuelve el valor de una clave en un diccionario."""
    if isinstance(value, dict):
        return value.get(arg)
    return None
