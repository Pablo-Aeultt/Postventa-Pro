from .models import Tecnico

def tecnico_context(request):
    tecnico = None
    tecnico_iniciales = ''
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        try:
            tecnico = Tecnico.objects.get(email__iexact=(user.email or ''))
        except Tecnico.DoesNotExist:
            try:
                tecnico = Tecnico.objects.get(rut=user.username)
            except Tecnico.DoesNotExist:
                tecnico = None
        if tecnico and tecnico.nombre:
            partes = tecnico.nombre.strip().split()
            tecnico_iniciales = ''.join([p[0].upper() for p in partes if p])
    return {
        'tecnico': tecnico,
        'tecnico_iniciales': tecnico_iniciales,
    }
