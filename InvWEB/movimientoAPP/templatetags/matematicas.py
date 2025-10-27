# movimientoAPP/templatetags/matematicas.py

from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplica el valor por el argumento."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        # Devolver el valor original en caso de error (ej: si es None o texto)
        return value

@register.filter
def div(value, arg):
    """Divide el valor por el argumento."""
    try:
        arg = float(arg)
        if arg == 0:
            return 0 # Evitar división por cero
        return float(value) / arg
    except (ValueError, TypeError):
        return value