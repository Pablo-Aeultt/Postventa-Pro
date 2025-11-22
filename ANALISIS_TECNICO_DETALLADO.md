# 🔧 ANÁLISIS TÉCNICO DETALLADO - PLATAFORMA DE POSTVENTA

**Versión:** 0.2  
**Fecha:** Noviembre 2025  
**Autor:** Equipo Técnico  
**Estado:** En Desarrollo  

---

## 📋 TABLA DE CONTENIDOS

1. [Arquitectura General](#arquitectura-general)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Estructura de Carpetas](#estructura-de-carpetas)
4. [Modelo de Datos Detallado](#modelo-de-datos-detallado)
5. [Arquitectura de Autenticación](#arquitectura-de-autenticación)
6. [Flujo de Solicitudes HTTP](#flujo-de-solicitudes-http)
7. [Capas de la Aplicación](#capas-de-la-aplicación)
8. [Componentes Principales](#componentes-principales)
9. [Base de Datos y Optimizaciones](#base-de-datos-y-optimizaciones)
10. [Seguridad y Validaciones](#seguridad-y-validaciones)
11. [Escalabilidad y Performance](#escalabilidad-y-performance)
12. [Consideraciones para Producción](#consideraciones-para-producción)

---

## ARQUITECTURA GENERAL

### 🏗️ Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         NAVEGADOR (CLIENTE)                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Bootstrap 5 | Chart.js | JavaScript Vanilla | Font Awesome │ │
│  │                    (Frontend Responsivo)                     │ │
│  └──────────────────────┬──────────────────────────────────────┘ │
└─────────────────────────┼────────────────────────────────────────┘
                          │ HTTP/HTTPS
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO 5.2.7 (Backend)                       │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │  URLs (urls.py)                                            │  │
│ │  └─ Enrutamiento de solicitudes                           │  │
│ └────────────────────────────────────────────────────────────┘  │
│                          ↓                                       │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │  VISTAS (views.py) - Controladores                         │  │
│ │  ├─ PropietarioViews (mis_reclamos, crear_reclamo)        │  │
│ │  ├─ TecnicoViews (dashboard, citas, completar_trabajo)    │  │
│ │  ├─ SupervisorViews (dashboard_kpis, reclamos, validar)   │  │
│ │  └─ AdminViews (gestión de datos)                         │  │
│ └────────────────────────────────────────────────────────────┘  │
│                          ↓                                       │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │  LÓGICA DE NEGOCIO                                         │  │
│ │  ├─ Autenticación (3 backends personalizados)             │  │
│ │  ├─ KPI Calculator (cálculos de métricas)                │  │
│ │  ├─ Notificaciones (emails automáticos)                   │  │
│ │  └─ Validaciones (RUT, formatos, permisos)               │  │
│ └────────────────────────────────────────────────────────────┘  │
│                          ↓                                       │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │  ORM DJANGO (models.py)                                    │  │
│ │  ├─ Perfil, Usuario, Propietario, Técnico                │  │
│ │  ├─ Reclamo (core), Cita, Encuesta                       │  │
│ │  ├─ GestionEscombros, UsoMaterial, Disponibilidad        │  │
│ │  └─ 45+ Migraciones aplicadas                            │  │
│ └────────────────────────────────────────────────────────────┘  │
│                          ↓                                       │
└──────────────────────────┼────────────────────────────────────────┘
                          │ SQL
                          ↓
        ┌──────────────────────────────────────┐
        │    SQLite3 Database (db.sqlite3)     │
        │  - 25+ Tablas                        │
        │  - Índices en campos clave          │
        │  - Constraints de integridad        │
        └──────────────────────────────────────┘
```

---

## STACK TECNOLÓGICO

### 🖥️ Backend Stack

```
┌────────────────────────────────────────────┐
│           BACKEND STACK                    │
├────────────────────────────────────────────┤
│ Python 3.11+                               │
│ Django Framework 5.2.7                     │
│  ├─ ORM (Object-Relational Mapping)       │
│  ├─ Autenticación (Auth + Backends)       │
│  ├─ Forms (Validación)                    │
│  ├─ Admin (Interfaz de administración)    │
│  └─ Middleware (Seguridad, CSRF, etc)    │
│                                           │
│ Base de Datos: SQLite3                    │
│  ├─ Desarrollo: ✓ (db.sqlite3)           │
│  └─ Producción: ✗ (Considerar PostgreSQL)│
│                                           │
│ Librerías Clave:                          │
│  ├─ Pillow 12.0.0 (Procesamiento imágenes)│
│  ├─ openpyxl 3.1.5 (Exportación Excel)   │
│  ├─ reportlab 4.4.5 (Generación PDF)     │
│  ├─ requests 2.32.3 (Cliente HTTP)       │
│  ├─ django-crispy-forms 2.4 (Form render)│
│  ├─ python-dateutil 2.9.0 (Fechas)       │
│  ├─ django-filter 24.3 (Filtrado)        │
│  ├─ django-cors-headers 4.4.0 (CORS)     │
│  └─ Werkzeug 3.0.1 (WSGI utilities)      │
└────────────────────────────────────────────┘
```

### 🎨 Frontend Stack

```
┌────────────────────────────────────────────┐
│           FRONTEND STACK                   │
├────────────────────────────────────────────┤
│ HTML5 (Django Templates)                   │
│  ├─ Herencia de templates                 │
│  ├─ Context processors                    │
│  └─ Auto-escaping (XSS prevention)        │
│                                           │
│ CSS Framework: Bootstrap 5                │
│  ├─ Responsive grid (12 columnas)         │
│  ├─ Componentes preconstruidos            │
│  ├─ Color scheme #1A4D4D (teal primario)  │
│  ├─ Color scheme #0d6efd (azul KPIs)      │
│  └─ Diseño Mobile-first                   │
│                                           │
│ JavaScript (Vanilla - Sin frameworks)     │
│  ├─ AJAX para carga dinámica              │
│  ├─ Event listeners para interactividad   │
│  ├─ Validación de formularios client-side │
│  └─ Calendarios interactivos              │
│                                           │
│ Librerías Frontend:                       │
│  ├─ Chart.js 3.9.1 (Gráficos)            │
│  ├─ Font Awesome 6 (Iconos)               │
│  └─ Bootstrap Icons (Iconos bootstrap)    │
└────────────────────────────────────────────┘
```

---

## ESTRUCTURA DE CARPETAS

```
Proyecto_postventa/
│
├── 📁 plataforma_postventa/          # Configuración Django
│   ├── settings.py                   # Configuración principal
│   ├── urls.py                       # Rutas principales
│   ├── wsgi.py                       # Entry point producción
│   └── asgi.py                       # Entry point async
│
├── 📁 postventa_app/                 # Aplicación principal
│   ├── 📁 migrations/                # 45+ migraciones
│   │   ├── 0001_initial.py
│   │   ├── 0002_reclamo_unidad.py
│   │   └── ...0045_perfil_rut.py
│   │
│   ├── 📁 templates/                 # Templates HTML
│   │   ├── base.html                 # Template base
│   │   ├── cliente_propietario/      # Vistas propietario
│   │   ├── tecnico/                  # Vistas técnico
│   │   ├── supervisor/               # Vistas supervisor
│   │   └── includes/                 # Componentes reutilizables
│   │       └── navbar.html
│   │
│   ├── 📁 static/                    # Archivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── 📁 management/commands/       # Comandos personalizados
│   │   └── commands/
│   │
│   ├── models.py                     # 25+ Modelos ORM (1025 líneas)
│   ├── views.py                      # 80+ Funciones vista (2927 líneas)
│   ├── urls.py                       # Rutas de app
│   ├── forms.py                      # Formularios Django
│   ├── admin.py                      # Interfaz admin
│   ├── apps.py                       # Configuración app
│   ├── backends.py                   # 3 Backends autenticación
│   ├── notificaciones.py             # Sistema de emails
│   ├── kpi_calculator.py             # Cálculos de KPIs
│   └── tests.py                      # Tests unitarios
│
├── 📁 scripts/                       # Scripts de utilidad
│   ├── crear_usuarios_propietarios.py
│   ├── crear_tecnicos.py
│   ├── crear_especialidades.py
│   └── ... (20+ scripts)
│
├── manage.py                         # CLI Django
├── requirements.txt                  # Dependencias Python
├── db.sqlite3                        # Base de datos SQLite
│
└── 📁 media/                         # Archivos subidos por usuarios
    ├── evidencias/                   # Fotos de reclamos
    └── fallas/

```

---

## MODELO DE DATOS DETALLADO

### 🗄️ Entidades Principales

#### 1. **Perfil (Tabla: auth_user + perfil)**

```python
class Perfil(models.Model):
    user = OneToOneField(User)          # FK a Django User
    rol = CharField(choices=[            # 4 tipos de rol
        'administrador',
        'supervisor',
        'tecnico',
        'propietario'
    ])
    rut = CharField(max_length=15)       # RUT/DNI
    telefono = CharField(max_length=30)
    direccion = CharField(max_length=200)
    proyecto = ForeignKey(Proyecto)      # Para supervisores
```

**Propósito:** Extender Django User con datos adicionales específicos de la aplicación.

**Relaciones:**
- 1:1 con User (autenticación Django)
- 0:1 con Proyecto (solo supervisores tienen)

**Índices:** PK(perfil.id), FK(proyecto_id)

---

#### 2. **Propietario (Tabla: propietario)**

```python
class Propietario(models.Model):
    user = OneToOneField(User)
    nombre = CharField(max_length=120)
    rut = CharField(max_length=12)
    tipo_propietario = CharField(choices=[
        'natural',      # Persona natural
        'juridica'      # Empresa
    ])
    email = EmailField()
    telefono = CharField(max_length=30)
    direccion = CharField(max_length=200)
    proyecto = ForeignKey(Proyecto)     # Vivienda del propietario
```

**Propósito:** Información específica de propietarios/clientes.

**Relaciones:**
- 1:1 con User
- N:1 con Proyecto
- 1:N con Reclamo (propietario → múltiples reclamos)

---

#### 3. **Técnico (Tabla: tecnico)**

```python
class Tecnico(models.Model):
    usuario = OneToOneField(User)
    constructora = ForeignKey(Constructora)
    especialidad = ForeignKey(Especialidad)
    telefono = CharField(max_length=30)
    estado = CharField(choices=[
        'disponible',
        'ocupado',
        'vacaciones'
    ])
```

**Propósito:** Información de técnicos y especialistas.

**Relaciones:**
- 1:1 con User
- N:1 con Constructora
- N:1 con Especialidad
- 1:N con Reclamo (asignación)
- 1:N con Disponibilidad (horarios)

---

#### 4. **Reclamo (Tabla: reclamo) - ENTIDAD CENTRAL**

```python
class Reclamo(models.Model):
    id_reclamo = AutoField(primary_key=True)
    numero_folio = CharField(unique=True)
    descripcion = TextField()
    resolucion = TextField(null=True)
    
    # Ubicación
    unidad = CharField(max_length=50)
    ubicacion_especifica = CharField(max_length=200)
    
    # Timeline
    fecha_ingreso = DateTimeField()
    fecha_resolucion = DateTimeField(null=True)
    fecha_asignacion = DateTimeField(null=True)
    
    # Estado
    estado = CharField(choices=[
        'ingresado',      # Inicial
        'asignado',       # Supervisor asignó técnico
        'en_ejecucion',   # Técnico trabaja
        'en_proceso',     # En revisión
        'completado',     # Técnico terminó
        'resuelto',       # Supervisor validó
        'cancelado'       # Cancelado
    ])
    
    # Prioridad y categoría
    prioridad = CharField(choices=['bajo', 'medio', 'alto', 'crítico'])
    categoria = ForeignKey(Especialidad)  # Tipo de trabajo
    
    # Asignaciones
    propietario = ForeignKey(Propietario)
    tecnico_asignado = ForeignKey(Tecnico, null=True)
    proyecto = ForeignKey(Proyecto)
    
    # Costos
    tiempo_estimado_horas = IntegerField(null=True)
    costo_total = DecimalField(null=True)  # Suma de materiales
```

**Propósito:** Entidad central que orbita todo el sistema.

**Flujo de Estados:**
```
ingresado → asignado → en_ejecucion → completado → resuelto
                          ↓
                      en_proceso
                       (revisión)
```

**Relaciones:**
- N:1 con Propietario
- N:1 con Técnico
- N:1 con Proyecto
- N:1 con Especialidad
- 1:N con Cita
- 1:N con ArchivoEvidencia
- 1:N con Encuesta
- 1:N con GestionEscombros
- 1:N con UsoMaterial

---

#### 5. **Cita (Tabla: cita)**

```python
class Cita(models.Model):
    reclamo = ForeignKey(Reclamo, on_delete=CASCADE)
    tecnico = ForeignKey(Tecnico, on_delete=SET_NULL, null=True)
    
    fecha_programada = DateField()
    hora_inicio = TimeField()
    hora_fin = TimeField()
    
    estado = CharField(choices=[
        'pendiente',      # Creada, esperando confirmación
        'confirmada',     # Confirmada por ambas partes
        'en_curso',       # Técnico inició visita
        'finalizada',     # Completada
        'cancelada'       # Cancelada
    ])
    
    # Duración real (se calcula después)
    hora_inicio_real = DateTimeField(null=True)
    hora_termino_real = DateTimeField(null=True)
    duracion_minutos = IntegerField(null=True)
```

**Propósito:** Programación de visitas técnicas.

**Relaciones:**
- N:1 con Reclamo
- N:1 con Técnico
- 1:1 con VisitaTecnica (datos de ejecución)

---

#### 6. **Disponibilidad (Tabla: disponibilidad)**

```python
class Disponibilidad(models.Model):
    tecnico = ForeignKey(Tecnico)
    
    # Recurrencia semanal
    dia_semana = IntegerField(choices=[
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo')
    ])
    
    hora_inicio = TimeField()      # Ej: 09:00
    hora_fin = TimeField()         # Ej: 17:00
    intervalo_minutos = IntegerField(default=30)  # Franjas de 30min
    
    fecha_inicio_vigencia = DateField()
    fecha_fin_vigencia = DateField(null=True)
    
    activo = BooleanField(default=True)
```

**Propósito:** Horarios recurrentes de técnicos para agendamiento.

**Funcionalidad:**
- Permite definir "Lunes a Viernes 09:00-17:00"
- Sistema genera slots de 30 minutos automáticamente
- Supervisor ve calendario visual
- Propietario elige horario disponible

---

#### 7. **ArchivoEvidencia (Tabla: archivo_evidencia)**

```python
class ArchivoEvidencia(models.Model):
    reclamo = ForeignKey(Reclamo, on_delete=CASCADE)
    
    archivo = FileField(upload_to='evidencias/')  # Foto
    tipo_fase = CharField(choices=[
        'antes',        # Estado inicial del defecto
        'durante',      # Durante reparación
        'despues'       # Resultado final
    ])
    
    subido_por = CharField(choices=[
        'propietario',  # Cliente reportó
        'tecnico',      # Técnico cargó
        'sistema'       # Automático
    ])
    
    descripcion = TextField(null=True)
    fecha_carga = DateTimeField(auto_now_add=True)
```

**Propósito:** Galería de fotos del reclamo.

**Almacenamiento:**
- Ruta: `/media/evidencias/reclamo_001_*.jpg`
- Storage personalizado preserva nombres originales
- Limite: 5MB por archivo
- Formatos: JPG, PNG, WebP

---

#### 8. **EncuestaSatisfaccion (Tabla: encuesta_satisfaccion)**

```python
class EncuestaSatisfaccion(models.Model):
    reclamo = ForeignKey(Reclamo)
    propietario = ForeignKey(Propietario)
    
    # Calificaciones
    satisfaccion_general = IntegerField(choices=range(1, 6))  # 1-5 estrellas
    puntualidad_tecnico = IntegerField(choices=range(1, 6))
    calidad_trabajo = IntegerField(choices=range(1, 6))
    
    # Pregunta binaria
    recomendaria = BooleanField()  # NPS: ¿Lo recomendarías?
    
    # Comentarios
    comentarios = TextField(null=True, blank=True)
    
    fecha_respuesta = DateTimeField(auto_now_add=True)
```

**Propósito:** Capturar satisfacción del cliente.

**Cálculos derivados:**
- Promedio general: `(satisf_gral + puntualidad + calidad) / 3`
- NPS: `% de propietarios que recomendarían`
- Análisis por técnico: agrega KPIs

---

#### 9. **GestionEscombros (Tabla: gestion_escombros)**

```python
class GestionEscombros(models.Model):
    reclamo = ForeignKey(Reclamo)
    
    tipo_escombro = CharField(max_length=100)  # "Polvo + cascajos"
    volumen = CharField(max_length=50)         # "1 bolsa", "2m³"
    empresa_retiro = ForeignKey(EmpresaRetiro)
    
    estado = CharField(choices=[
        'pendiente_validacion',    # Técnico registró, esperando supervisor
        'aprobado',                # Supervisor aprobó
        'en_transito',             # Empresa retirando
        'completado'               # Retiro realizado
    ])
    
    costo_estimado = DecimalField(null=True)
    fecha_retiro_programada = DateField(null=True)
    fecha_retiro_real = DateField(null=True)
```

**Propósito:** Auditoría de residuos generados.

**Flujo:**
1. Técnico registra después de trabajar
2. Supervisor valida (verifica tipo, volumen, empresa)
3. Empresa retira escombros
4. Sistema registra confirmación

---

#### 10. **UsoMaterial (Tabla: uso_material)**

```python
class UsoMaterial(models.Model):
    reclamo = ForeignKey(Reclamo)
    material = CharField(max_length=100)  # "Pintura blanca mate"
    cantidad = DecimalField(max_digits=10, decimal_places=2)
    unidad = CharField(max_length=20)     # "litros", "kg", "paquete"
    costo_unitario = DecimalField(max_digits=10, decimal_places=2)
    costo_total = DecimalField(  # Cantidad × Costo unitario
        max_digits=10,
        decimal_places=2
    )
    categoria_material = CharField(choices=[
        'pintura',
        'selladores',
        'adhesivos',
        'herramientas',
        'otros'
    ])
```

**Propósito:** Inventario de consumibles por reclamo.

**Funcionalidad:**
- Técnico registra post-trabajo
- Cálculo automático de totales
- Base para análisis de costos
- Genera reportes de consumo

---

### 📊 Diagrama ER (Entity-Relationship)

```
                    ┌─────────────┐
                    │   Usuario   │ (Django User)
                    │  (auth_user)│
                    └──────┬──────┘
                           │ 1:1
              ┌────────────┴──────────────┐
              │                           │
         ┌────▼────┐              ┌──────▼──────┐
         │  Perfil │              │ Propietario │
         └────┬────┘              └──────┬──────┘
              │                          │ N:1
         (rol: super                 ┌───▼────┐
          tecn, prop)            ┌───┤Proyecto├─────┐
                                 │   └────────┘     │
                            ┌────▼────┐       ┌─────▼────┐
                            │ Reclamo │◄──┐   │Constructo│
                            │ (CORE)  │   │   │    ra    │
                            └────┬────┘   │   └──────────┘
                                 │       │
            ┌────────────────────┼───────┘
            │                    │
       ┌────▼────┐        ┌─────▼──────┐
       │   Cita  │        │   Tecnico  │
       └────┬────┘        └─────┬──────┘
            │                   │ N:1
       ┌────▼──────────────┐    │
       │ VisitaTecnica     │ ◄──┤
       │ (detalles ejecuc) │    │
       └───────────────────┘    │
                            ┌───▼────────┐
                            │Disponibilid│
                            │     ad     │
                            └────────────┘

       ┌──────────────────────────┐
       │     Reclamo (HUB)        │
       │    (id_reclamo = PK)     │
       ├──────────────────────────┤
       │ - ArchivoEvidencia (1:N) │
       │ - Encuesta (1:N)         │
       │ - GestionEscombros (1:N) │
       │ - UsoMaterial (1:N)      │
       │ - VisitaTecnica (1:N)    │
       └──────────────────────────┘
```

---

## ARQUITECTURA DE AUTENTICACIÓN

### 🔐 Sistema Multi-Backend

```python
# backends.py - 3 Backends Personalizados

class SupervisorBackend(ModelBackend):
    """
    Autentica supervisores verificando:
    1. Usuario existe en auth.User
    2. Tiene Perfil.rol == 'supervisor'
    """
    def authenticate(self, request, username=None, password=None):
        # Verifica username/email + contraseña
        # Luego verifica Perfil.rol == 'supervisor'
        # Retorna User si es válido

class TecnicoBackend(ModelBackend):
    """
    Autentica técnicos con soporte para RUT:
    1. Normaliza RUT (quita puntos/guiones)
    2. Busca en auth.User.username
    3. Verifica contraseña
    4. Valida Perfil.rol == 'tecnico'
    """
    def authenticate(self, request, username=None, password=None):
        # Intenta normalizar RUT
        rut_limpio = limpiar_rut(username)
        # Busca usuario con ese RUT
        # Verifica password
        # Valida perfil

class PropietarioBackend(ModelBackend):
    """
    Autentica propietarios con creación automática:
    1. Busca por RUT en Propietario
    2. Si existe, autentica
    3. Si no existe pero RUT válido, crea automáticamente
    """
    def authenticate(self, request, username=None, password=None):
        # Busca Propietario por RUT
        # Si no existe y RUT válido, crea nuevo usuario
        # Enlaza con Propietario
        # Retorna Usuario autenticado
```

**Flujo de Autenticación:**

```
┌─────────────────────────────────────┐
│  Usuario entra credenciales         │
│  username: "pablo_martinez"         │
│  password: "segura123"              │
└────────────────┬────────────────────┘
                 │
         ┌───────▼────────┐
         │ AUTHENTICATION │
         │  PROCESS       │
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
  Intent: SupervisorBackend
    │            │            │
    ├─ ¿Usuario existe?
    │ └─ auth.User.username = 'pablo_martinez'
    │    ✓ Encontrado
    │
    ├─ ¿Contraseña correcta?
    │ └─ check_password('segura123', user.password)
    │    ✓ Válida
    │
    └─ ¿Tiene Perfil.rol == 'supervisor'?
       └─ Perfil.objects.get(user=user).rol
          ✓ 'supervisor'

              ↓
         ✅ LOGIN EXITOSO
         Redirige a dashboard_supervisor
```

**Backends Probados (En Orden):**

```python
AUTHENTICATION_BACKENDS = [
    'postventa_app.backends.SupervisorBackend',
    'postventa_app.backends.TecnicoBackend',
    'postventa_app.backends.PropietarioBackend',
    'django.contrib.auth.backends.ModelBackend',  # Default Django
]
```

Django intenta cada uno en orden hasta encontrar uno válido.

---

## FLUJO DE SOLICITUDES HTTP

### 📡 Ciclo Completo: Crear Reclamo

```
┌────────────────────────────────────────────────────────────┐
│  1. NAVEGADOR - GET /crear-reclamo/                       │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  2. URL ROUTING (urls.py)                                 │
│     path('crear-reclamo/', views.crear_reclamo)          │
│     → Encuentra función view correspondiente              │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  3. MIDDLEWARE CHAIN                                      │
│     ├─ SecurityMiddleware        (headers seguros)        │
│     ├─ SessionMiddleware         (sesión usuario)         │
│     ├─ AuthenticationMiddleware  (verifica login)         │
│     ├─ CsrfViewMiddleware        (token CSRF)             │
│     └─ MessageMiddleware         (mensajes flash)         │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  4. DECORADORES DE VISTA                                  │
│     @login_required               (¿Usuario autenticado?)  │
│     └─ Redirige a login si NO                            │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  5. VISTA (views.py)                                      │
│  def crear_reclamo(request):                             │
│    ├─ GET:  render(form vacío)                          │
│    └─ POST: procesa formulario                          │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  6. FORMULARIO (forms.py)                                 │
│     class ReclamoForm(ModelForm):                        │
│     ├─ Validación de campos                             │
│     ├─ Validación de negocio                            │
│     └─ Limpieza de datos                                │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  7. LÓGICA DE NEGOCIO (views.py)                          │
│     ├─ Obtener propietario autenticado                   │
│     ├─ Validar permisos (¿propietario?)                  │
│     ├─ Procesar archivos adjuntos                        │
│     ├─ Crear registro Reclamo                           │
│     └─ Guardar ArchivoEvidencia                         │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  8. ORM DJANGO (models.py)                                │
│     reclamo = Reclamo(                                    │
│         propietario=propietario,                         │
│         estado='ingresado',                              │
│         fecha_ingreso=now(),                             │
│         ...                                              │
│     )                                                    │
│     reclamo.save()  ← Genera INSERT SQL                 │
│                                                         │
│     # Archivos                                           │
│     archivo = ArchivoEvidencia(                          │
│         reclamo=reclamo,                                │
│         archivo=file,                                   │
│         subido_por='propietario'                        │
│     )                                                   │
│     archivo.save()  ← Genera INSERT SQL                 │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  9. DATABASE (SQLite3)                                    │
│                                                          │
│  INSERT INTO reclamo (                                  │
│    numero_folio, descripcion, estado, fecha_ingreso...  │
│  ) VALUES ('REC-001', '...', 'ingresado', '2025-11-21')│
│                                                          │
│  INSERT INTO archivo_evidencia (                        │
│    reclamo_id, archivo, subido_por, fecha_carga         │
│  ) VALUES (1, '/media/evidencias/foto.jpg', 'prop...') │
│                                                          │
│  ✅ Transacción completada                              │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  10. NOTIFICACIONES (notificaciones.py)                   │
│      ├─ Email a Propietario: confirmación              │
│      └─ Email a Supervisor: nuevo reclamo             │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  11. RESPUESTA HTTP                                       │
│      ├─ Status: 302 (Redirect)                           │
│      ├─ Location: /mis-reclamos/                         │
│      └─ Headers: Set-Cookie (sesión)                    │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  12. NAVEGADOR                                            │
│      ├─ Sigue redirect a /mis-reclamos/                 │
│      ├─ Carga nuevo HTML                                │
│      ├─ Ejecuta CSS/JavaScript                          │
│      └─ Renderiza con datos nuevos del reclamo          │
└────────────────────────────────────────────────────────────┘
```

---

## CAPAS DE LA APLICACIÓN

### 🏢 Arquitectura en Capas

```
┌────────────────────────────────────────────────────────┐
│          PRESENTATION LAYER (Django Templates)        │
│  ├─ base.html (template base)                         │
│  ├─ cliente_propietario/ (vistas propietario)         │
│  ├─ tecnico/ (vistas técnico)                         │
│  ├─ supervisor/ (vistas supervisor)                   │
│  └─ includes/ (componentes reutilizables)             │
└────────────────────────────────────────────────────────┘
                       ↑ render()
                       │
┌────────────────────────────────────────────────────────┐
│        PRESENTATION LOGIC LAYER (Context Processors)  │
│  ├─ tecnico_context() (inyecta datos técnico)         │
│  ├─ supervisor_context() (inyecta KPIs)               │
│  └─ navbar_context() (datos navegación)               │
└────────────────────────────────────────────────────────┘
                       ↑
                       │
┌────────────────────────────────────────────────────────┐
│           CONTROLLER LAYER (views.py)                 │
│  ├─ Maneja requests HTTP                             │
│  ├─ Llama a lógica de negocio                        │
│  ├─ Maneja autenticación/autorización                │
│  ├─ Procesa archivos                                 │
│  ├─ Renderiza templates                              │
│  └─ 80+ funciones vista (2927 líneas)               │
└────────────────────────────────────────────────────────┘
                       ↑
                       │
┌────────────────────────────────────────────────────────┐
│      BUSINESS LOGIC LAYER (kpi_calculator.py)         │
│  ├─ KPICalculator (calcula 15 KPIs)                  │
│  ├─ Cálculos de satisfacción                         │
│  ├─ Análisis de eficiencia                           │
│  ├─ Lógica de estados/transiciones                   │
│  └─ Validaciones de negocio complejas                │
└────────────────────────────────────────────────────────┘
                       ↑
                       │
┌────────────────────────────────────────────────────────┐
│      SERVICE LAYER (notificaciones.py)                │
│  ├─ EmailTemplates (genera emails)                    │
│  ├─ Envío de notificaciones                           │
│  ├─ SMS/Webhooks (futuro)                            │
│  └─ Integración externa                              │
└────────────────────────────────────────────────────────┘
                       ↑
                       │
┌────────────────────────────────────────────────────────┐
│         DATA LAYER (models.py + ORM)                  │
│  ├─ 25+ Modelos Django                               │
│  ├─ Querysets y filtros                              │
│  ├─ Validaciones de modelo                           │
│  ├─ Signals (post_save, pre_save)                   │
│  └─ Custom managers                                  │
└────────────────────────────────────────────────────────┘
                       ↑
                       │
┌────────────────────────────────────────────────────────┐
│         DATABASE LAYER (SQLite3)                      │
│  ├─ 25+ Tablas                                        │
│  ├─ Índices                                           │
│  ├─ Constraints                                       │
│  └─ Transactions                                      │
└────────────────────────────────────────────────────────┘
```

---

## COMPONENTES PRINCIPALES

### 🔧 Componentes Clave

#### 1. **KPI Calculator**

```python
class KPICalculator:
    """
    Calcula 15 KPIs en tiempo real
    """
    def __init__(self, proyecto):
        self.proyecto = proyecto
    
    def reclamos_abiertos(self):
        """Reclamos no resueltos"""
        return Reclamo.objects.filter(
            proyecto=self.proyecto,
            estado__in=['ingresado', 'asignado', 
                       'en_ejecucion', 'completado']
        ).count()
    
    def satisfaccion_promedio(self):
        """Promedio de estrellas (1-5)"""
        return EncuestaSatisfaccion.objects.filter(
            reclamo__proyecto=self.proyecto
        ).aggregate(
            promedio=Avg('satisfaccion_general')
        )['promedio']
    
    def tasa_resolucion(self):
        """(Resueltos / Total) × 100"""
        total = Reclamo.objects.filter(
            proyecto=self.proyecto
        ).count()
        resueltos = Reclamo.objects.filter(
            proyecto=self.proyecto,
            estado='resuelto'
        ).count()
        return (resueltos / total * 100) if total > 0 else 0
    
    # 12 KPIs más...
```

#### 2. **Email Template Engine**

```python
class EmailTemplates:
    @staticmethod
    def reclamo_asignado(propietario, reclamo, tecnico):
        """Genera email cuando reclamo es asignado"""
        asunto = f"Reclamo #{reclamo.id_reclamo} asignado"
        mensaje = f"""
        Hola {propietario.nombre},
        
        Tu reclamo ha sido asignado al técnico {tecnico.usuario.first_name}.
        Pronto se contactará contigo para agendar una visita.
        
        Detalles: {reclamo.descripcion}
        """
        return {'asunto': asunto, 'mensaje': mensaje}
```

#### 3. **Storage Personalizado**

```python
class NombreOriginalStorage(FileSystemStorage):
    """
    Preserva el nombre original del archivo
    en lugar de renombrarlo automáticamente
    """
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            # Agrega contador: foto_1.jpg, foto_2.jpg
            dir_name, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            counter = 1
            while True:
                new_name = f'{file_root}_{counter}{file_ext}'
                # ...
        return name
```

---

## BASE DE DATOS Y OPTIMIZACIONES

### 📊 Estadísticas de BD

```
Tipo:           SQLite3 (db.sqlite3)
Tamaño actual:  ~50 MB (con datos de prueba)
Tablas:         25+
Columnas:       150+
Índices:        30+
Migraciones:    45

Datos Actuales:
├─ Usuarios:              15
├─ Propietarios:          8
├─ Técnicos:              8
├─ Supervisores:          3
├─ Proyectos:             3
├─ Reclamos:             100+
├─ Citas:                150+
├─ Archivos Evidencia:   300+
└─ Encuestas:            80+
```

### 🚀 Optimizaciones Aplicadas

```python
# 1. QUERYSET OPTIMIZATION
# ❌ Sin optimizar (N+1 queries)
reclamos = Reclamo.objects.all()
for reclamo in reclamos:
    propietario = reclamo.propietario  # Query por cada reclamo!

# ✅ Optimizado (select_related)
reclamos = Reclamo.objects.select_related(
    'propietario',      # FK
    'tecnico_asignado'  # FK
).prefetch_related(
    'citas',            # Reverse FK
    'archivos_evidencia'
)

# 2. INDEXES
class Reclamo(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['proyecto', 'estado']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['propietario', 'estado']),
        ]

# 3. PAGINATION (en vistas con muchos datos)
from django.core.paginator import Paginator

reclamos = Reclamo.objects.all()
paginator = Paginator(reclamos, 25)  # 25 por página
page = request.GET.get('page')
reclamos_paginados = paginator.get_page(page)

# 4. LAZY EVALUATION
# Las queries se ejecutan solo cuando se necesitan
reclamos_query = Reclamo.objects.filter(estado='resuelto')
# No se ejecuta SQL todavía
for reclamo in reclamos_query:  # Ahora sí se ejecuta
    print(reclamo.id_reclamo)

# 5. AGGREGATION (en lugar de loops en Python)
# ❌ Lento: Traer 1000 reclamos a Python, sumarlos
total_costo = sum([r.costo_total for r in Reclamo.objects.all()])

# ✅ Rápido: Sumar en BD
from django.db.models import Sum
total_costo = Reclamo.objects.aggregate(
    total=Sum('costo_total')
)['total']
```

### 🔍 Índices Principales

```sql
-- Índices automáticos de Django
CREATE INDEX reclamo_proyecto_id ON reclamo(proyecto_id);
CREATE INDEX reclamo_tecnico_id ON reclamo(tecnico_asignado_id);
CREATE INDEX reclamo_propietario_id ON reclamo(propietario_id);

-- Índices de búsqueda/filtrado
CREATE INDEX reclamo_estado ON reclamo(estado);
CREATE INDEX reclamo_fecha_ingreso ON reclamo(fecha_ingreso);
CREATE INDEX cita_tecnico_fecha ON cita(tecnico_id, fecha_programada);
CREATE INDEX disponibilidad_tecnico_dia ON disponibilidad(tecnico_id, dia_semana);
```

---

## SEGURIDAD Y VALIDACIONES

### 🛡️ Capas de Seguridad

```
┌────────────────────────────────────────────┐
│  1. CAPA TRANSPORT                         │
│  └─ HTTPS/TLS (producción)                 │
│     - Certificado SSL/TLS                  │
│     - Encriptación en tránsito              │
├────────────────────────────────────────────┤
│  2. CAPA AUTENTICACIÓN                     │
│  ├─ Contraseñas: pbkdf2 hasheadas         │
│  ├─ Sessions: Django sessions middleware   │
│  ├─ CSRF tokens: Prevención de CSRF        │
│  └─ 3 Backends de autenticación            │
├────────────────────────────────────────────┤
│  3. CAPA AUTORIZACIÓN                      │
│  ├─ @login_required (solo usuarios)       │
│  ├─ Verificación de rol en vista           │
│  ├─ Permisos por proyecto (Supervisor)     │
│  └─ Validación de propietario en datos    │
├────────────────────────────────────────────┤
│  4. CAPA VALIDACIÓN                        │
│  ├─ ValidationError en modelos             │
│  ├─ Django Forms validación               │
│  ├─ Regex para RUT                         │
│  ├─ Límites de tamaño de archivo          │
│  └─ Whitelist de extensiones               │
├────────────────────────────────────────────┤
│  5. CAPA ORM                               │
│  ├─ SQL Injection prevenido (ORM)         │
│  ├─ Parametrized queries                   │
│  └─ No raw SQL                             │
├────────────────────────────────────────────┤
│  6. CAPA TEMPLATE                          │
│  ├─ Auto-escaping de variables             │
│  ├─ XSS prevention                         │
│  └─ |escape filter donde necesario         │
└────────────────────────────────────────────┘
```

### 🔐 Validaciones Específicas

```python
# 1. RUT Validation
def validate_rut(value: str):
    if value is None:
        return
    s = str(value).strip()
    if not re.match(r"^[0-9.\-kK]+$", s):
        raise ValidationError(
            "RUT inválido: use números, puntos y guion (ej: 12.345.678-9)"
        )

# 2. File Upload Validation
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']

if request.FILES['evidencia'].size > MAX_UPLOAD_SIZE:
    raise ValidationError("Archivo demasiado grande")

# 3. Permission Check
def supervisor_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        supervisor = get_supervisor_from_user(request.user)
        if not supervisor:
            messages.error(request, "No tienes acceso como supervisor")
            return redirect('mis_reclamos')
        return view_func(request, *args, **kwargs)
    return wrapper

# 4. Business Logic Validation
if reclamo.propietario.user != request.user:
    messages.error(request, "No tienes permiso para ver este reclamo")
    return redirect('mis_reclamos')
```

---

## ESCALABILIDAD Y PERFORMANCE

### 📈 Limitaciones Actuales (SQLite)

| Aspecto | SQLite | Producción (PostgreSQL) |
|---------|--------|------------------------|
| **Usuarios Concurrentes** | 5-10 | 1000+ |
| **Conexiones** | 1 simultánea | Múltiples |
| **Throughput (reqs/sec)** | 10-20 | 1000+ |
| **Tamaño DB** | ✓ hasta 2GB | Terabytes |
| **Full-text search** | ✗ Limitado | ✓ Excelente |
| **Replication** | ✗ No | ✓ Sí |
| **Backups en vivo** | ✗ No | ✓ Sí |

### 🚀 Plan de Escalamiento

**Fase 1: Optimización (Actual → 100 usuarios)**
```
✓ Índices en campos clave
✓ Query optimization (select_related, prefetch_related)
✓ Caching con Redis
✓ Paginar resultados grandes
✓ Comprimir imágenes
```

**Fase 2: Migración (100 → 1000 usuarios)**
```
- PostgreSQL en lugar de SQLite
- Connection pooling (pgBouncer)
- Caché distribuido (Redis)
- Static files a CDN
- Imagenes a servicio cloud (AWS S3)
```

**Fase 3: Infraestructura (1000+ usuarios)**
```
- Load balancing (nginx, HAProxy)
- Múltiples servidores app
- Replicación de BD (Primary-Replica)
- Message queue (Celery + RabbitMQ)
- Search engine (Elasticsearch)
```

---

## CONSIDERACIONES PARA PRODUCCIÓN

### ⚠️ Cambios Necesarios

```python
# 1. settings.py
DEBUG = False  # Nunca en producción
ALLOWED_HOSTS = ['tudominio.com', 'www.tudominio.com']

# 2. Base de Datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postventa_prod',
        'USER': 'postgres',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '5432',
    }
}

# 3. Seguridad
SECRET_KEY = os.getenv('SECRET_KEY')  # Desde variable de entorno
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

# 4. Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')

# 5. Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    },
}

# 6. Archivos Estáticos
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/postventa/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# 7. Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/postventa/media/'

# 8. Backups
# Cron job diario
0 2 * * * pg_dump postventa_prod > /backups/db_$(date +\%Y\%m\%d).sql
```

### 🐳 Containerización (Docker)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Comando de inicio
CMD ["gunicorn", "plataforma_postventa.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DB_HOST=db
      - DB_PASSWORD=postgres
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: postventa_prod
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

volumes:
  postgres_data:
```

---

## 📊 MÉTRICAS Y MONITOREO

### Métricas Clave de Sistema

```
Performance:
├─ Tiempo promedio respuesta: < 200ms
├─ P99 latencia: < 500ms
├─ Throughput: 100+ req/seg
├─ Disponibilidad: 99.9%
└─ Error rate: < 0.1%

Database:
├─ Conexiones activas: < 50
├─ Queries lentas (> 100ms): < 5/minuto
├─ Índices no usados: revisar mensualmente
└─ Tamaño BD: monitorear crecimiento

Aplicación:
├─ Errores no capturados: 0
├─ Logs de auditoría: completos
├─ Tasa de login fallido: < 1%
└─ Sesiones activas: variable

Negocio:
├─ Reclamos ingresados: KPI
├─ Satisfacción media: > 4.0⭐
├─ Tiempo resolución: < 5 días
└─ NPS: > 60%
```

---

## 🔄 PRÓXIMOS PASOS

### Mejoras Recomendadas

```
CORTO PLAZO (1-2 meses):
├─ Migración a PostgreSQL
├─ Implementar caching con Redis
├─ Agregar tests automatizados
├─ Documentación API REST
└─ Configuración de CI/CD

MEDIANO PLAZO (2-6 meses):
├─ API REST (Django REST Framework)
├─ Autenticación JWT
├─ Websockets para notificaciones en tiempo real
├─ App móvil (React Native)
└─ Geolocalización de técnicos

LARGO PLAZO (6-12 meses):
├─ Machine Learning para predicciones
├─ Integración con sistemas externos (SAP, etc)
├─ Data warehouse para BI
├─ Marketplace de técnicos
└─ Gamificación de métricas
```

---

## 📚 REFERENCIAS

**Documentación:**
- Django 5.2: https://docs.djangoproject.com/
- PostgreSQL: https://www.postgresql.org/docs/
- SQLite: https://www.sqlite.org/docs.html

**Archivos del Proyecto:**
- `models.py` - Estructura de datos (1025 líneas)
- `views.py` - Lógica de aplicación (2927 líneas)
- `settings.py` - Configuración
- `requirements.txt` - Dependencias

**Análisis Relacionados:**
- `DESCRIPCION_PLATAFORMA_COMPLETA.md` - Vista usuario
- `ANALISIS_PROYECTO.md` - Análisis funcional

---

**Autor:** Equipo Técnico  
**Última Actualización:** Noviembre 2025  
**Estado:** v0.2 - En Desarrollo Activo

