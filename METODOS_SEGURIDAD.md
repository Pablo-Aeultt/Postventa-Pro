# 🔐 MÉTODOS Y ESTRATEGIAS DE SEGURIDAD - PLATAFORMA DE POSTVENTA

**Versión:** 0.2  
**Fecha:** Noviembre 2025  
**Clasificación:** Documentación Técnica  
**Última Actualización:** Noviembre 2025

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Autenticación](#autenticación)
3. [Autorización y Control de Acceso](#autorización-y-control-de-acceso)
4. [Protección de Datos](#protección-de-datos)
5. [Validación de Entrada](#validación-de-entrada)
6. [Protección contra Ataques Comunes](#protección-contra-ataques-comunes)
7. [Seguridad de Sesiones](#seguridad-de-sesiones)
8. [Criptografía](#criptografía)
9. [Auditoría y Logging](#auditoría-y-logging)
10. [Gestión de Archivos](#gestión-de-archivos)
11. [Comunicaciones Seguras](#comunicaciones-seguras)
12. [Checklist de Seguridad para Producción](#checklist-de-seguridad-para-producción)

---

## RESUMEN EJECUTIVO

### 🎯 Objetivo de Seguridad

La plataforma implementa un **modelo de defensa en profundidad** con múltiples capas de seguridad:

```
┌─────────────────────────────────────────────────┐
│  CAPA 7: LÓGICA DE NEGOCIO VALIDADA            │
├─────────────────────────────────────────────────┤
│  CAPA 6: AUTORIZACIÓN POR ROL                   │
├─────────────────────────────────────────────────┤
│  CAPA 5: VALIDACIÓN DE FORMULARIOS              │
├─────────────────────────────────────────────────┤
│  CAPA 4: MIDDLEWARE DJANGO                      │
├─────────────────────────────────────────────────┤
│  CAPA 3: AUTENTICACIÓN DE MÚLTIPLES BACKENDS   │
├─────────────────────────────────────────────────┤
│  CAPA 2: TRANSPORTE SEGURO (HTTPS)             │
├─────────────────────────────────────────────────┤
│  CAPA 1: FIREWALL Y NETWORK                     │
└─────────────────────────────────────────────────┘
```

### 📊 Matriz de Seguridad

| Aspecto | Implementación | Estado | Nivel |
|--------|---|---|---|
| **Autenticación** | 3 backends personalizados | ✅ Implementado | Alto |
| **Autorización** | RBAC por rol | ✅ Implementado | Alto |
| **Encriptación Datos** | pbkdf2 + Django | ✅ Implementado | Muy Alto |
| **CSRF Protection** | Token CSRF | ✅ Implementado | Muy Alto |
| **SQL Injection** | ORM Django | ✅ Protegido | Muy Alto |
| **XSS Prevention** | Auto-escaping | ✅ Implementado | Muy Alto |
| **Validación Entrada** | Django Forms + Regex | ✅ Implementado | Alto |
| **HTTPS/TLS** | ⚠️ No en desarrollo | 🔧 Producción | Crítico |
| **Logging de Seguridad** | Básico | ⚠️ Limitado | Medio |
| **Rate Limiting** | No implementado | ❌ Faltante | Recomendado |

---

## AUTENTICACIÓN

### 🔐 Sistema de Autenticación Multi-Backend

La plataforma implementa **3 backends personalizados** que permiten múltiples formas de login:

#### 1️⃣ **SupervisorBackend**

```python
# File: postventa_app/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from postventa_app.models import Perfil

User = get_user_model()

class SupervisorBackend(ModelBackend):
    """
    Backend de autenticación para supervisores.
    Autentica usando email/username y verifica rol.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Intenta autenticar supervisor por username/email
        """
        # Intentar buscar por username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Intentar por email
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        
        # Verificar contraseña
        if user.check_password(password) and self.user_can_authenticate(user):
            # Verificar que tiene rol de supervisor
            try:
                perfil = user.perfil
                if perfil.rol == 'supervisor':
                    return user
            except Perfil.DoesNotExist:
                return None
        
        return None
    
    def get_user(self, user_id):
        """Obtener usuario por ID"""
        try:
            user = User.objects.get(pk=user_id)
            perfil = user.perfil
            if perfil.rol == 'supervisor':
                return user
        except User.DoesNotExist:
            pass
        return None
```

**Flujo de Autenticación Supervisor:**
```
┌─────────────────────────────────────────┐
│  Usuario: email@example.com             │
│  Contraseña: ••••••••                   │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │ Buscar usuario │
         └───────┬────────┘
                 │
         ┌───────▼────────────────┐
         │ ¿Existe en BD?         │
         │ ✓ Sí                   │
         └───────┬────────────────┘
                 │
         ┌───────▼────────────────┐
         │ check_password()        │
         │ ✓ Coincide              │
         └───────┬────────────────┘
                 │
         ┌───────▼────────────────┐
         │ Verificar Perfil.rol   │
         │ ✓ rol == 'supervisor'  │
         └───────┬────────────────┘
                 │
              ✅ LOGIN ÉXITOSO
```

---

#### 2️⃣ **TecnicoBackend**

```python
class TecnicoBackend(ModelBackend):
    """
    Backend para técnicos.
    Soporta login por RUT (normaliza formato).
    """
    
    def limpiar_rut(self, rut):
        """
        Normaliza RUT eliminando puntos y guiones.
        
        Ejemplos:
        - "12.345.678-9" → "123456789"
        - "123456789"    → "123456789"
        - "1234567-8"    → "12345678"
        """
        if not rut:
            return None
        
        # Convertir a mayúsculas y quitar espacios
        rut = str(rut).upper().strip()
        
        # Eliminar puntos
        rut = rut.replace('.', '')
        
        # Eliminar guiones
        rut = rut.replace('-', '')
        
        return rut
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica técnico por RUT o email
        """
        if not username or not password:
            return None
        
        # Intentar limpiar RUT
        rut_limpio = self.limpiar_rut(username)
        
        try:
            # Buscar por username (que puede ser RUT limpio)
            user = User.objects.get(username=rut_limpio)
        except User.DoesNotExist:
            # Intentar por email
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                # Intentar buscar usuario con ese RUT en Tecnico
                from postventa_app.models import Tecnico, Perfil
                try:
                    tecnico = Tecnico.objects.get(usuario__username=rut_limpio)
                    user = tecnico.usuario
                except Tecnico.DoesNotExist:
                    return None
        
        # Verificar contraseña
        if user.check_password(password) and self.user_can_authenticate(user):
            # Verificar perfil
            try:
                perfil = user.perfil
                if perfil.rol == 'tecnico':
                    return user
            except Perfil.DoesNotExist:
                return None
        
        return None
    
    def get_user(self, user_id):
        """Obtener usuario técnico"""
        try:
            user = User.objects.get(pk=user_id)
            if user.perfil.rol == 'tecnico':
                return user
        except User.DoesNotExist:
            pass
        return None
```

**Normalización de RUT - Ejemplos:**

| Entrada | Salida | Válido |
|---------|--------|--------|
| `12.345.678-9` | `123456789` | ✅ |
| `123456789` | `123456789` | ✅ |
| `1234567-8` | `12345678` | ✅ |
| `12.345.678-K` | `123456789K` | ✅ |
| `ABC` | `ABC` | ❌ |

---

#### 3️⃣ **PropietarioBackend**

```python
class PropietarioBackend(ModelBackend):
    """
    Backend para propietarios.
    CARACTERÍSTICA ESPECIAL: Crea usuario automáticamente si no existe.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica propietario.
        Si no existe pero el RUT es válido, crea automáticamente.
        """
        if not username or not password:
            return None
        
        from postventa_app.models import Propietario
        import re
        
        # Limpiar RUT
        rut_limpio = self.limpiar_rut(username)
        
        try:
            # Intentar buscar propietario por RUT
            propietario = Propietario.objects.get(rut=rut_limpio)
            user = propietario.user
            
            # Verificar contraseña
            if user.check_password(password):
                return user
            
        except Propietario.DoesNotExist:
            # ⭐ CARACTERÍSTICA: Crear propietario automático
            # Validar que sea un RUT válido
            if self.es_rut_valido(rut_limpio):
                # Crear nuevo usuario y propietario
                from django.contrib.auth.models import User
                
                nuevo_username = f"prop_{rut_limpio}"
                
                # Generar hash de contraseña temporal
                user = User()
                user.username = nuevo_username
                user.set_password(password)
                user.save()
                
                # Crear propietario
                propietario = Propietario.objects.create(
                    user=user,
                    rut=rut_limpio,
                    nombre="Propietario Nuevo",  # Se completa después
                    email=f"{rut_limpio}@example.com"
                )
                
                return user
        
        return None
    
    def es_rut_valido(self, rut):
        """
        Validación básica de RUT (no verifica dígito verificador).
        Solo valida formato.
        """
        if not rut or len(rut) < 7:
            return False
        
        # Debe tener números y opcionalmente 'K' al final
        import re
        if re.match(r'^\d{7,9}[0-9K]?$', rut):
            return True
        
        return False
    
    def limpiar_rut(self, rut):
        """Limpia formato RUT"""
        if not rut:
            return None
        rut = str(rut).upper().strip()
        rut = rut.replace('.', '').replace('-', '')
        return rut
    
    def get_user(self, user_id):
        """Obtener usuario propietario"""
        try:
            user = User.objects.get(pk=user_id)
            if user.perfil.rol == 'propietario':
                return user
        except User.DoesNotExist:
            pass
        return None
```

**Característica Especial del PropietarioBackend:**

```
┌─────────────────────────────┐
│ Propietario intenta login   │
│ RUT: 12.345.678-9           │
│ (No existe en BD)           │
└────────────────┬────────────┘
                 │
        ┌────────▼─────────┐
        │ ¿RUT válido?     │
        │ ✓ Sí             │
        └────────┬─────────┘
                 │
        ┌────────▼──────────────────┐
        │ CREAR automáticamente:     │
        │ - Usuario Django          │
        │ - Perfil                  │
        │ - Propietario             │
        └────────┬──────────────────┘
                 │
              ✅ LOGIN ÉXITOSO
              (Primer ingreso)
```

---

### 🔄 Orden de Intento de Backends

```python
# settings.py

AUTHENTICATION_BACKENDS = [
    'postventa_app.backends.SupervisorBackend',   # Intenta primero
    'postventa_app.backends.TecnicoBackend',      # Luego
    'postventa_app.backends.PropietarioBackend',  # Después
    'django.contrib.auth.backends.ModelBackend',  # Default Django
]
```

**Flujo:**
```
Usuario envía credenciales
        ↓
SupervisorBackend.authenticate()
    ├─ ¿Es supervisor? → ✅ Devolver user
    └─ Si no → Siguiente
        ↓
TecnicoBackend.authenticate()
    ├─ ¿Es técnico? → ✅ Devolver user
    └─ Si no → Siguiente
        ↓
PropietarioBackend.authenticate()
    ├─ ¿Es propietario? → ✅ Devolver user
    ├─ ¿RUT válido pero no existe? → ✅ Crear y devolver user
    └─ Si no → Siguiente
        ↓
ModelBackend (Django default)
    └─ Último intento de autenticación estándar
```

---

### 🔑 Manejo de Contraseñas

```python
# Django maneja las contraseñas de forma segura

# 1. HASH DE CONTRASEÑA (pbkdf2)
# Django NO almacena las contraseñas en texto plano

# Cuando se crea un usuario:
user = User.objects.create_user(
    username='pablo',
    email='pablo@example.com',
    password='MiContraseña123'  # Se hashea automáticamente
)

# La contraseña se almacena como:
# pbkdf2_sha256$720000$randomsalt$hashedpassword

# 2. VERIFICACIÓN DE CONTRASEÑA
# Cuando el usuario intenta login:
if user.check_password(password_ingresada):
    # Las contraseñas coinciden
    # Django computa el hash y compara
    pass

# 3. ALGORITMO POR DEFECTO
# Django 5.2 usa: PBKDF2 (Password-Based Key Derivation Function 2)
# - 720,000 iteraciones
- Salt aleatorio
# - SHA256

# 4. CONFIGURACIÓN PERSONALIZADA (opcional)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Más fuerte
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]
```

---

## AUTORIZACIÓN Y CONTROL DE ACCESO

### 👥 Sistema de Roles (RBAC)

```python
# models.py

class Perfil(models.Model):
    ROLES = [
        ('administrador', 'Administrador'),
        ('supervisor', 'Supervisor'),
        ('tecnico', 'Técnico'),
        ('propietario', 'Propietario'),
    ]
    
    user = OneToOneField(User, on_delete=CASCADE)
    rol = CharField(max_length=20, choices=ROLES)
    rut = CharField(max_length=15, blank=True, null=True)
    telefono = CharField(max_length=30, blank=True, null=True)
    proyecto = ForeignKey(Proyecto, null=True, blank=True)
```

### 🛡️ Decoradores de Autorización

```python
# views.py

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def supervisor_required(view_func):
    """
    Verifica que el usuario sea un supervisor.
    Redirige a login si no está autenticado o no es supervisor.
    """
    @wraps(view_func)
    @login_required  # Primero verifica login
    def wrapper(request, *args, **kwargs):
        # Obtener supervisor
        supervisor = get_supervisor_from_user(request.user)
        
        # Verificar que existe y tiene proyecto asignado
        if not supervisor or not supervisor.proyecto:
            messages.error(
                request, 
                'No tienes acceso como supervisor o no tienes proyecto asignado.'
            )
            return redirect('login')
        
        # Añadir supervisor al request para usar en la vista
        request.supervisor = supervisor
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def tecnico_required(view_func):
    """
    Verifica que el usuario sea un técnico.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        tecnico = get_tecnico_from_user(request.user)
        
        if not tecnico:
            messages.error(request, 'No tienes acceso como técnico.')
            return redirect('login')
        
        request.tecnico = tecnico
        return view_func(request, *args, **kwargs)
    
    return wrapper

def propietario_required(view_func):
    """
    Verifica que el usuario sea un propietario.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        propietario = get_cliente_from_user(request.user)
        
        if not propietario:
            messages.error(request, 'No tienes acceso como propietario.')
            return redirect('login')
        
        request.propietario = propietario
        return view_func(request, *args, **kwargs)
    
    return wrapper
```

### 📍 Verificación de Permisos en Vistas

```python
# Ejemplo: Ver un reclamo específico

@login_required
def ver_reclamo(request, reclamo_id):
    """
    Un propietario solo puede ver sus propios reclamos.
    Un técnico solo puede ver reclamos asignados.
    Un supervisor puede ver todos los de su proyecto.
    """
    
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    propietario = get_cliente_from_user(request.user)
    tecnico = get_tecnico_from_user(request.user)
    supervisor = get_supervisor_from_user(request.user)
    
    # PROPIETARIO: Solo sus reclamos
    if propietario:
        if reclamo.propietario != propietario:
            messages.error(request, 'No tienes permiso para ver este reclamo.')
            return redirect('mis_reclamos')
    
    # TÉCNICO: Solo los asignados
    elif tecnico:
        if reclamo.tecnico_asignado != tecnico:
            messages.error(request, 'Este reclamo no está asignado a ti.')
            return redirect('tecnico_dashboard')
    
    # SUPERVISOR: Solo de su proyecto
    elif supervisor:
        if reclamo.proyecto != supervisor.proyecto:
            messages.error(request, 'No tienes acceso a este proyecto.')
            return redirect('dashboard_supervisor')
    
    # ADMIN: Puede ver todo (simplemente no entra en las restricciones)
    
    return render(request, 'detalle_reclamo.html', {'reclamo': reclamo})
```

### 🔐 Matriz de Permisos

| Acción | Propietario | Técnico | Supervisor | Admin |
|--------|---|---|---|---|
| **Crear Reclamo** | ✅ Sus propios | ❌ | ❌ | ✅ |
| **Ver Reclamo** | ✅ Sus propios | ✅ Asignados | ✅ Su proyecto | ✅ |
| **Editar Reclamo** | ⚠️ Ingresado | ✅ Si asignado | ✅ Su proyecto | ✅ |
| **Asignar Técnico** | ❌ | ❌ | ✅ Su proyecto | ✅ |
| **Validar Escombro** | ❌ | ❌ | ✅ Su proyecto | ✅ |
| **Ver Dashboard KPI** | ❌ | ✅ Propios | ✅ Su proyecto | ✅ |
| **Exportar Reportes** | ❌ | ❌ | ✅ Su proyecto | ✅ |
| **Gestionar Usuarios** | ❌ | ❌ | ❌ | ✅ |
| **Acceder a Admin** | ❌ | ❌ | ❌ | ✅ |

---

## PROTECCIÓN DE DATOS

### 🔐 Encriptación en Reposo

```python
# Datos sensibles que se protegen:

# 1. CONTRASEÑAS (Hasheadas con PBKDF2)
# Nunca se almacenan en texto plano
# Hash: pbkdf2_sha256$720000$salt$hash

# 2. RUT/DNI (Opcional: encriptar)
# Actualmente: Almacenado en texto plano (considerar encripción)
# Recomendación para producción:
from django.contrib.postgres.fields import CIText

class Propietario(models.Model):
    rut = models.CharField(max_length=15)  # ⚠️ Considerar encriptación
    email = models.EmailField()  # ✅ Protegido por SSL en tránsito

# 3. DATOS FINANCIEROS
# Costo de reclamos, materiales
# Recomendación: Usar django-encrypted-model-fields

from encrypted_model_fields.fields import EncryptedCharField

class UsoMaterial(models.Model):
    costo_unitario = EncryptedCharField()
    costo_total = EncryptedCharField()

# 4. NOTAS PRIVADAS
# Observaciones internas de supervisor
# Recomendación: Encriptar notas sensibles

class NotaInternaReclamo(models.Model):
    reclamo = ForeignKey(Reclamo)
    contenido = EncryptedTextField()
    creado_por = ForeignKey(User)
    fecha_creacion = DateTimeField(auto_now_add=True)
```

### 🛡️ Protección de Datos Personales

```python
# Cumplimiento de normativas (GDPR, LGPD, etc.)

# 1. CONSENTIMIENTO
# Guardar consentimiento para recolectar datos
class Consentimiento(models.Model):
    usuario = ForeignKey(User)
    tipo = CharField(choices=[
        ('marketing', 'Marketing'),
        ('analytics', 'Análisis'),
        ('datos_personales', 'Datos Personales'),
    ])
    aceptado = BooleanField()
    fecha = DateTimeField(auto_now_add=True)

# 2. DERECHO AL OLVIDO
# Posibilidad de eliminar datos
def solicitar_eliminacion_datos(request):
    """Un usuario puede solicitar eliminar todos sus datos"""
    user = request.user
    propietario = get_cliente_from_user(user)
    
    # Anonimizar datos en lugar de eliminar (mejor para auditoría)
    propietario.nombre = "ELIMINADO"
    propietario.email = f"deleted_{propietario.id}@example.com"
    propietario.rut = "ELIMINADO"
    propietario.save()
    
    # Eliminar archivos
    ArchivoEvidencia.objects.filter(
        reclamo__propietario=propietario
    ).delete()

# 3. PORTABILIDAD DE DATOS
# Exportar datos del usuario
def exportar_datos_usuario(request):
    """Descargar todos los datos personales en JSON"""
    user = request.user
    propietario = get_cliente_from_user(user)
    
    datos = {
        'usuario': {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
        },
        'propietario': {
            'nombre': propietario.nombre,
            'rut': propietario.rut,
            'telefono': propietario.telefono,
        },
        'reclamos': [
            {
                'id': r.id_reclamo,
                'descripcion': r.descripcion,
                'estado': r.estado,
                'fecha_ingreso': r.fecha_ingreso.isoformat(),
            }
            for r in propietario.reclamo_set.all()
        ]
    }
    
    response = JsonResponse(datos)
    response['Content-Disposition'] = 'attachment; filename="mis_datos.json"'
    return response
```

---

## VALIDACIÓN DE ENTRADA

### ✅ Validación en Capas

```python
# CAPA 1: DJANGO FORMS

class ReclamoForm(ModelForm):
    """
    Valida datos antes de guardar en BD
    """
    class Meta:
        model = Reclamo
        fields = ['proyecto', 'unidad', 'categoria', 'descripcion']
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validación personalizada
        descripcion = cleaned_data.get('descripcion', '')
        if len(descripcion) < 10:
            raise ValidationError(
                "La descripción debe tener al menos 10 caracteres"
            )
        
        if len(descripcion) > 2000:
            raise ValidationError(
                "La descripción no puede exceder 2000 caracteres"
            )
        
        return cleaned_data

# CAPA 2: MODELO

class Reclamo(models.Model):
    descripcion = TextField(
        validators=[
            MinLengthValidator(10),
            MaxLengthValidator(2000),
        ]
    )
    prioridad = CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^(bajo|medio|alto|crítico)$',
                message='Prioridad inválida'
            )
        ]
    )

# CAPA 3: VISTA

@login_required
def crear_reclamo(request):
    if request.method == 'POST':
        form = ReclamoForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Datos ya validados
            reclamo = form.save(commit=False)
            reclamo.propietario = get_cliente_from_user(request.user)
            reclamo.save()
            
            messages.success(request, 'Reclamo creado exitosamente.')
            return redirect('mis_reclamos')
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return render(request, 'crear_reclamo.html', {'form': form})
```

### 🔍 Validaciones Específicas

```python
# 1. VALIDACIÓN DE RUT

def validate_rut(value: str):
    """
    Valida formato básico de RUT chileno.
    No valida dígito verificador (es responsabilidad de importación).
    """
    if value is None:
        return
    
    s = str(value).strip()
    if not s:
        return
    
    # Solo números, puntos, guiones y K
    if not re.match(r"^[0-9.\-kK]+$", s):
        raise ValidationError(
            "RUT inválido: use números, puntos y guion (ej: 12.345.678-9)"
        )

class Propietario(models.Model):
    rut = CharField(max_length=12, validators=[validate_rut])

# 2. VALIDACIÓN DE EMAIL

from django.core.validators import EmailValidator

class User(models.Model):
    email = EmailField(validators=[EmailValidator()])

# 3. VALIDACIÓN DE TELÉFONO

def validate_telefono(value):
    """Valida formato de teléfono"""
    # Aceptar: +56 9 1234 5678, 912345678, +56912345678
    if not re.match(r'^(\+56)?[\d\s\-()]+$', str(value)):
        raise ValidationError("Formato de teléfono inválido")

class Tecnico(models.Model):
    telefono = CharField(max_length=20, validators=[validate_telefono])

# 4. VALIDACIÓN DE FECHAS

def validate_fecha_futura(value):
    """Valida que la fecha sea futura"""
    if value < timezone.now().date():
        raise ValidationError("La fecha debe ser futura")

class Cita(models.Model):
    fecha_programada = DateField(validators=[validate_fecha_futura])

# 5. VALIDACIÓN DE ARCHIVOS

def validate_archivo_evidencia(file):
    """
    Valida tamaño y tipo de archivo
    """
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    
    if file.size > MAX_SIZE:
        raise ValidationError(f"Archivo demasiado grande. Máximo: 5MB")
    
    if file.content_type not in ALLOWED_TYPES:
        raise ValidationError(
            f"Tipo de archivo no permitido. "
            f"Permitidos: JPG, PNG, WebP, GIF"
        )
    
    # Verificar extensión del archivo
    ext = file.name.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        raise ValidationError("Extensión de archivo no permitida")

class ArchivoEvidencia(models.Model):
    archivo = FileField(
        upload_to='evidencias/',
        validators=[validate_archivo_evidencia]
    )
```

---

## PROTECCIÓN CONTRA ATAQUES COMUNES

### 🛡️ CSRF (Cross-Site Request Forgery)

```python
# Django protege contra CSRF automáticamente

# 1. EN FORMULARIOS (HTML)
<form method="POST" action="/crear-reclamo/">
    {% csrf_token %}  <!-- Token CSRF -->
    <input type="text" name="descripcion">
    <button type="submit">Crear</button>
</form>

# 2. EN AJAX
# Obtener token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Usar en fetch
fetch('/api/crear-reclamo/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        descripcion: 'Mi defecto',
        categoria: 1,
    })
})

# 3. MIDDLEWARE (automático)
# En settings.py:
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',  # ✅ Activo
    ...
]

# 4. CONFIGURACIÓN DE SEGURIDAD
CSRF_COOKIE_SECURE = True  # Solo HTTPS (producción)
CSRF_COOKIE_HTTPONLY = True  # No accesible desde JS
CSRF_TRUSTED_ORIGINS = ['https://tudominio.com']
```

### 🔓 SQL Injection

```python
# ❌ VULNERABLE (NUNCA hacer esto)
rut = request.GET.get('rut')
query = f"SELECT * FROM propietario WHERE rut = '{rut}'"
# Si rut = "'; DROP TABLE propietario; --"
# Ejecutaría: DROP TABLE propietario

# ✅ SEGURO (Usar ORM Django)
rut = request.GET.get('rut')
propietarios = Propietario.objects.filter(rut=rut)
# Django sanitiza la entrada automáticamente

# ✅ SEGURO (Si necesitas SQL crudo)
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM propietario WHERE rut = %s",
        [rut]  # Parámetro separado
    )
    result = cursor.fetchall()

# NUNCA:
# cursor.execute(f"SELECT * FROM propietario WHERE rut = '{rut}'")
```

### 🔗 XSS (Cross-Site Scripting)

```python
# ❌ VULNERABLE
# Template sin escape
<p>{{ user_comment }}</p>
# Si user_comment = "<script>alert('XSS')</script>"
# Se ejecutaría el script

# ✅ SEGURO (Auto-escape activado)
# Django escapa automáticamente por defecto
<p>{{ user_comment }}</p>
# Resultado: &lt;script&gt;alert('XSS')&lt;/script&gt;

# ✅ EXPLÍCITO (Marcar como seguro si es necesario)
from django.utils.safestring import mark_safe

# Usar mark_safe SOLO si confías en la fuente
safe_html = mark_safe(confiable_html)
<div>{{ safe_html|safe }}</div>

# ✅ ESCAPAR EN JAVASCRIPT
import json
context = {
    'user_data': json.dumps({
        'nombre': nombre_usuario,
        'email': email_usuario,
    })
}
<script>
    const userData = {{ user_data|safe }};
    // JSON.stringify maneja escaping automático
</script>

# ✅ ESCAPAR EN ATRIBUTOS
<a href="{{ url|urlencode }}">Link</a>

# ✅ ESCAPAR EN CSS
# Los valores CSS se escapan automáticamente
<div style="color: {{ color }};">Text</div>
```

### 🎭 Clickjacking

```python
# Django protege contra Clickjacking automáticamente

# Middleware en settings.py:
MIDDLEWARE = [
    ...
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # ✅ Activo
    ...
]

# Configuración:
X_FRAME_OPTIONS = 'DENY'  # No permitir iframe

# O más flexible:
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Solo mismo origen

# Por vista específica:
from django.views.decorators.clickjacking import xframe_options_deny

@xframe_options_deny
def vista_sensible(request):
    return render(request, 'template.html')
```

### 🔓 XXE (XML External Entity)

```python
# ⚠️ Riesgo si se procesa XML

# ❌ VULNERABLE
import xml.etree.ElementTree as ET
xml_data = request.FILES['archivo'].read()
tree = ET.parse(xml_data)
# XXE attack: <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>

# ✅ SEGURO (Desactivar resolución de entidades)
import xml.etree.ElementTree as ET
from defusedxml import ElementTree as DefusedET

xml_data = request.FILES['archivo'].read()
tree = DefusedET.parse(xml_data)  # Seguro contra XXE
```

---

## SEGURIDAD DE SESIONES

### 🔐 Gestión de Sesiones

```python
# settings.py

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# Las sesiones se guardan en BD (seguro)

SESSION_COOKIE_AGE = 1200  # 20 minutos
# Las sesiones expiran después de inactividad

SESSION_COOKIE_SECURE = True  # Solo HTTPS (producción)
# No se envía por HTTP sin encripción

SESSION_COOKIE_HTTPONLY = True  # No accesible desde JavaScript
# Protege contra XSS

SESSION_COOKIE_SAMESITE = 'Strict'  # Protege contra CSRF
# Solo se envía con requests del mismo sitio

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# Sesión persiste incluso si se cierra el navegador

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

### 🚪 Cierre de Sesión

```python
# views.py

@login_required
def logout_view(request):
    """
    Cierra sesión de forma segura
    """
    # Obtener datos antes de logout (opcional)
    usuario = request.user.username
    
    # Destruir sesión completamente
    logout(request)  # Django limpia la sesión
    
    # Limpiar cookies específicamente (extra seguro)
    response = redirect('login')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    
    messages.info(request, 'Has cerrado sesión correctamente.')
    return response

# Logout forzado por expiración
def session_expiry_warning(request):
    """Advertencia de expiración de sesión"""
    if request.user.is_authenticated:
        # Verificar última actividad
        last_activity = request.session.get('last_activity')
        if last_activity:
            from datetime import timedelta
            from django.utils import timezone
            
            diferencia = timezone.now() - last_activity
            if diferencia > timedelta(minutes=15):
                # Sesión expiró
                logout(request)
                messages.warning(
                    request, 
                    'Tu sesión ha expirado por inactividad.'
                )
                return redirect('login')
        
        # Actualizar última actividad
        request.session['last_activity'] = timezone.now()
```

### 🔄 Prevención de Fijación de Sesión

```python
# Django cambia el ID de sesión después del login automáticamente

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Django cambia automáticamente el session ID aquí
            login(request, user)
            # Nuevo session ID: diferente al pre-login
            
            return redirect('dashboard')
    
    return render(request, 'login.html', {'form': form})
```

---

## CRIPTOGRAFÍA

### 🔐 Algoritmos Implementados

```python
# 1. HASHING DE CONTRASEÑAS (PBKDF2)

# Default en Django 5.2
# Algoritmo: PBKDF2-SHA256
# Iteraciones: 720,000 (iteraciones altas = más seguro, más lento)
# Salt: Aleatorio por contraseña

from django.contrib.auth.hashers import make_password, check_password

# Crear hash
password = "MiContraseña123"
hashed = make_password(password)
# Resultado: pbkdf2_sha256$720000$abc123def456$hashedvalue

# Verificar
if check_password(password, hashed):
    print("Contraseña correcta")

# 2. TOKENS CSRF
# Generados aleatoriamente, vinculados a sesión
# Verificados en cada POST/PUT/DELETE

from django.middleware.csrf import get_token
token = get_token(request)
# Token nuevo para cada sesión

# 3. GENERACIÓN DE TOKENS ALEATORIOS (para links de reset, etc)

from django.utils.crypto import get_random_string

# Token para reset de contraseña
reset_token = get_random_string(32)  # 32 caracteres aleatorios
# Recomendación: guardar hash del token en BD, no el token mismo

# 4. GENERACIÓN DE SECRETOS

from secrets import token_urlsafe

# Para APIs o integraciones
api_key = token_urlsafe(32)  # Más seguro que get_random_string
```

---

## AUDITORÍA Y LOGGING

### 📝 Logging de Seguridad

```python
# settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/security.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'postventa_app': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}
```

### 📊 Eventos de Auditoría

```python
# views.py

import logging

logger = logging.getLogger(__name__)

def login_view(request):
    """Registra intentos de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log: Login exitoso
            logger.info(
                f"LOGIN_SUCCESS: usuario={user.username}, ip={get_client_ip(request)}"
            )
            
            return redirect('dashboard')
        else:
            # Log: Login fallido
            logger.warning(
                f"LOGIN_FAILED: username={username}, ip={get_client_ip(request)}"
            )
    
    return render(request, 'login.html')

def crear_reclamo(request):
    """Registra creación de reclamos"""
    if request.method == 'POST':
        form = ReclamoForm(request.POST, request.FILES)
        if form.is_valid():
            reclamo = form.save()
            
            # Log: Auditoría
            logger.info(
                f"RECLAMO_CREADO: "
                f"reclamo_id={reclamo.id_reclamo}, "
                f"usuario={request.user.username}, "
                f"propietario={reclamo.propietario.nombre}"
            )

def cambiar_estado_reclamo(request, reclamo_id):
    """Registra cambios de estado"""
    reclamo = get_object_or_404(Reclamo, id_reclamo=reclamo_id)
    estado_anterior = reclamo.estado
    
    # ... cambiar estado ...
    
    reclamo.estado = nuevo_estado
    reclamo.save()
    
    # Log: Cambio de estado
    logger.info(
        f"RECLAMO_CAMBIO_ESTADO: "
        f"reclamo_id={reclamo_id}, "
        f"de={estado_anterior}, "
        f"a={nuevo_estado}, "
        f"usuario={request.user.username}"
    )
```

### 📋 Tabla de Auditoría (Modelo)

```python
class LogAuditoria(models.Model):
    TIPOS_EVENTO = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('crear_reclamo', 'Crear Reclamo'),
        ('editar_reclamo', 'Editar Reclamo'),
        ('asignar_tecnico', 'Asignar Técnico'),
        ('cambio_estado', 'Cambio de Estado'),
        ('cargar_evidencia', 'Cargar Evidencia'),
        ('validar_escombro', 'Validar Escombro'),
        ('acceso_denegado', 'Acceso Denegado'),
        ('cambio_contrasena', 'Cambio Contraseña'),
    ]
    
    usuario = ForeignKey(User, on_delete=SET_NULL, null=True)
    tipo_evento = CharField(max_length=30, choices=TIPOS_EVENTO)
    descripcion = TextField()
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    
    timestamp = DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['tipo_evento', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.tipo_evento} - {self.usuario} - {self.timestamp}"

# Guardar evento en BD
def registrar_evento(usuario, tipo, descripcion, request):
    """Guarda evento en tabla de auditoría"""
    LogAuditoria.objects.create(
        usuario=usuario,
        tipo_evento=tipo,
        descripcion=descripcion,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

# Usar en vistas
def login_view(request):
    # ...
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        
        registrar_evento(
            user, 
            'login', 
            f'Login exitoso', 
            request
        )
```

---

## GESTIÓN DE ARCHIVOS

### 📁 Seguridad en Carga de Archivos

```python
# 1. VALIDACIÓN DE TIPO

import mimetypes

def validate_imagen(file):
    """Valida que sea una imagen real"""
    # Verificar MIME type
    mime_type, _ = mimetypes.guess_type(file.name)
    
    if mime_type not in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
        raise ValidationError("Solo se permiten imágenes")
    
    # Verificar "magic bytes" (firma del archivo)
    file.seek(0)
    header = file.read(12)
    
    # Firmas conocidas
    valid_headers = [
        b'\xFF\xD8\xFF',      # JPG
        b'\x89PNG\r\n\x1a\n',  # PNG
        b'RIFF',               # WebP
        b'GIF87a', b'GIF89a',  # GIF
    ]
    
    file.seek(0)
    for header_valid in valid_headers:
        if header.startswith(header_valid):
            return
    
    raise ValidationError("El archivo no es una imagen válida")

# 2. ALMACENAMIENTO SEGURO

# settings.py
MEDIA_ROOT = '/var/www/postventa/media/'  # Fuera del root web
MEDIA_URL = '/media/'

# Configuración de nginx
# location /media/ {
#     alias /var/www/postventa/media/;
#     # Evitar ejecutar scripts en /media
#     types {
#         text/plain;
#     }
# }

# 3. NOMBRES DE ARCHIVO SEGUROS

import os
from django.utils.text import slugify
from django.utils.crypto import get_random_string

def generar_nombre_archivo_seguro(original_filename):
    """
    Genera nombre seguro para archivo.
    Evita path traversal y caracteres peligrosos.
    """
    # Obtener extensión
    _, ext = os.path.splitext(original_filename)
    
    # Generar nombre aleatorio
    nombre_seguro = get_random_string(32)
    
    # Nombre final: random_hash.ext
    return f"{nombre_seguro}{ext}"

class ArchivoEvidencia(models.Model):
    def archivo_path(instance, filename):
        """Genera ruta segura"""
        nombre_seguro = generar_nombre_archivo_seguro(filename)
        # Ruta: evidencias/2025/11/random_hash.jpg
        return f'evidencias/{instance.reclamo.id_reclamo}/{nombre_seguro}'
    
    archivo = FileField(upload_to=archivo_path)

# 4. PREVENCIÓN DE PATH TRAVERSAL

# ❌ VULNERABLE
filename = request.GET.get('file')
filepath = os.path.join(MEDIA_ROOT, filename)
# Si filename = "../../etc/passwd" → acceso no autorizado

# ✅ SEGURO
filename = request.GET.get('file')
# Validar que filename no contiene ../ o /
if '..' in filename or filename.startswith('/'):
    raise ValidationError("Nombre de archivo inválido")

# O usar basename
filename = os.path.basename(filename)  # Solo el nombre, sin ruta
filepath = os.path.join(MEDIA_ROOT, filename)

# 5. LÍMITES DE TAMAÑO

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

def validate_tamanio_archivo(file):
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            f"Archivo demasiado grande. "
            f"Máximo: {MAX_UPLOAD_SIZE / 1024 / 1024}MB, "
            f"Tu archivo: {file.size / 1024 / 1024:.2f}MB"
        )
```

---

## COMUNICACIONES SEGURAS

### 🔒 HTTPS/TLS

```python
# settings.py (PRODUCCIÓN)

# Forzar HTTPS
SECURE_SSL_REDIRECT = True

# Headers de seguridad
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "cdn.jsdelivr.net"),
    'style-src': ("'self'", "cdn.jsdelivr.net"),
}

# Certificado SSL
# Usar Let's Encrypt (gratuito)
# Renovación automática con certbot
```

### 📧 Email Seguro

```python
# settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')  # smtp.gmail.com, etc
EMAIL_PORT = 587  # TLS
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Usar variables de entorno, NUNCA hardcodear

# Envío de email seguro
from django.core.mail import send_mail

def enviar_email_seguro(destinatario, asunto, mensaje):
    """Envía email de forma segura"""
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[destinatario],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")
        # No revelar detalles al usuario
        raise ValidationError("Error enviando email. Intenta más tarde.")
```

---

## CHECKLIST DE SEGURIDAD PARA PRODUCCIÓN

### ✅ Antes de Deployar

```markdown
## 1. CONFIGURACIÓN DJANGO

- [ ] DEBUG = False
- [ ] SECRET_KEY con valor fuerte (no hardcodeado)
- [ ] ALLOWED_HOSTS configurado
- [ ] SECURE_SSL_REDIRECT = True
- [ ] SESSION_COOKIE_SECURE = True
- [ ] CSRF_COOKIE_SECURE = True
- [ ] SECURE_HSTS_SECONDS = 31536000

## 2. BASE DE DATOS

- [ ] Migración a PostgreSQL
- [ ] Backups diarios automatizados
- [ ] Contraseñas de BD fuertes
- [ ] BD en servidor separado
- [ ] Firewall restringiendo acceso a BD
- [ ] Replicación configurada

## 3. AUTENTICACIÓN

- [ ] HTTPS/TLS en todas las rutas
- [ ] Certificado SSL válido
- [ ] Password reset funcionando
- [ ] 2FA implementado (recomendado)
- [ ] Rate limiting en login
- [ ] Logging de intentos fallidos

## 4. ARCHIVOS Y ALMACENAMIENTO

- [ ] /media/ fuera del root web
- [ ] Permisos correctos en carpetas
- [ ] Backups de archivos cargados
- [ ] S3/CDN para escala
- [ ] Validación de tipo de archivo
- [ ] Límites de tamaño aplicados

## 5. SEGURIDAD RED

- [ ] Firewall configurado
- [ ] Puertos solo necesarios abiertos
- [ ] DDoS protection
- [ ] WAF (Web Application Firewall)
- [ ] Monitoreo de tráfico

## 6. MONITOREO Y LOGGING

- [ ] Logging de auditoría completo
- [ ] Alertas de errores
- [ ] Monitoreo de recursos
- [ ] Backup de logs
- [ ] Retención de logs: 90 días mínimo

## 7. MANTENCIÓN

- [ ] Updater de Django automático
- [ ] Parches de seguridad aplicados
- [ ] Vulnerabilidades checadas (safety)
- [ ] Tests de seguridad ejecutados
- [ ] Penetration testing anual

## 8. CUMPLIMIENTO LEGAL

- [ ] Política de privacidad
- [ ] Términos de servicio
- [ ] GDPR/LGPD cumplida
- [ ] Consentimiento de datos
- [ ] Derecho al olvido
- [ ] Portabilidad de datos
```

### 🔍 Escaneo de Vulnerabilidades

```bash
# Verificar vulnerabilidades conocidas
pip install safety
safety check

# Analizar código estático
pip install bandit
bandit -r postventa_app/

# Analizar seguridad Django
python manage.py check --deploy

# Escaneo OWASP
pip install django-owasp-zap-scan
python manage.py owasp_scan
```

---

## 📊 RESUMEN DE MEDIDAS DE SEGURIDAD

| Capa | Medida | Estado | Implementación |
|------|--------|--------|---|
| **Transporte** | HTTPS/TLS | 🔧 Producción | nginx + certbot |
| **Autenticación** | Multi-backend | ✅ Activo | 3 backends |
| **Contraseñas** | PBKDF2-SHA256 | ✅ Activo | Django default |
| **Sesiones** | Secure cookies | ✅ Activo | Django sessions |
| **CSRF** | Token CSRF | ✅ Activo | Middleware |
| **SQL Injection** | ORM Django | ✅ Activo | Parametrized queries |
| **XSS** | Auto-escape | ✅ Activo | Django templates |
| **Autorización** | RBAC | ✅ Activo | 4 roles |
| **Validación** | 3 capas | ✅ Activo | Forms + Modelos |
| **Archivos** | Validación + Storage | ✅ Activo | Helpers |
| **Logging** | Auditoría completa | ⚠️ Básico | LogAuditoria |
| **Rate Limiting** | No implementado | ❌ Faltante | django-ratelimit |
| **2FA** | No implementado | ❌ Faltante | django-otp |

---

## 🚀 PRÓXIMAS MEJORAS DE SEGURIDAD

```
CORTO PLAZO (1-2 semanas):
├─ Implementar Rate Limiting
├─ Configurar HTTPS/TLS
├─ Audit logging completo
└─ Cambiar SQLite → PostgreSQL

MEDIANO PLAZO (1-2 meses):
├─ Autenticación 2FA
├─ API Key Management
├─ Encryption at rest
├─ Penetration testing
└─ Security headers

LARGO PLAZO (3-6 meses):
├─ JWT authentication
├─ OAuth2 integration
├─ Zero-trust security model
├─ SIEM (Security Information Event Management)
└─ Certificación de seguridad
```

---

**Autor:** Equipo de Seguridad  
**Fecha:** Noviembre 2025  
**Clasificación:** Documentación Técnica - Confidencial  
**Versión:** 1.0

