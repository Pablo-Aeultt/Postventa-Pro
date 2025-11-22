from django import template
from ..models import Propietario

register = template.Library()

@register.filter
def propietario_for_user(user):
    """Devuelve el Propietario asociado a un User (por email o username->rut), o None."""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    # intentar por email
    try:
        return Propietario.objects.get(email__iexact=(user.email or ''))
    except Propietario.DoesNotExist:
        pass
    username = (getattr(user, 'username', '') or '').strip()
    username_clean = username.replace('.', '').replace('-', '')
    if username_clean:
        for p in Propietario.objects.all():
            if (p.rut or '').replace('.', '').replace('-', '').lower() == username_clean.lower():
                return p
    return None
