from django import template

register = template.Library()

@register.filter
def dict_lookup(dictionary, key):
    """Accede a un diccionario usando una clave"""
    if dictionary is None:
        return None
    return dictionary.get(key, [])

@register.filter
def mul(value, arg):
    """Multiplica dos números"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Accede a un elemento de un diccionario o lista"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key) if isinstance(dictionary, dict) else dictionary[key]
    except (KeyError, TypeError, IndexError):
        return None

@register.filter
def is_percentage(value):
    """Verifica si el valor parece ser un porcentaje (entre 0 y 100)"""
    try:
        val = float(value)
        return 0 <= val <= 100
    except (ValueError, TypeError):
        return False

@register.filter
def slugify_custom(value):
    """Convierte un string a slug-safe format"""
    if not value:
        return ""
    return str(value).lower().replace(" ", "-").replace("(", "").replace(")", "")
