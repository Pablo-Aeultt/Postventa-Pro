# ANÁLISIS DEL PROYECTO: PLATAFORMA DE POSTVENTA

## 1. DESCRIPCIÓN GENERAL

**Nombre:** Sistema de Gestión de Postventa
**Versión:** 0.2
**Tecnología:** Django 5.2.7 + SQLite3 + Bootstrap 5
**Propósito:** Plataforma SaaS para gestionar reclamos, citas, técnicos y satisfacción de clientes en proyectos inmobiliarios

---

## 2. ARQUITECTURA DE USUARIOS Y ROLES

El sistema maneja **4 roles principales**:

### 2.1 PROPIETARIO (Cliente Final)
- **Acceso:** Porta puerta en proyectos inmobiliarios
- **Funciones:**
  - Crear reclamos de defectos
  - Ver estado de sus reclamos
  - Ver citas programadas
  - Calificar satisfacción post-visita
  - Adjuntar evidencia fotográfica

### 2.2 TÉCNICO (Especialista)
- **Acceso:** Dashboard técnico
- **Funciones:**
  - Ver reclamos asignados
  - Confirmar/reprogramar citas
  - Marcar trabajos como completados
  - Registrar disponibilidad laboral
  - Ver historial de trabajos
  - Registrar escombros y materiales

### 2.3 SUPERVISOR (Gestor de Proyecto)
- **Acceso:** Dashboard supervisor por proyecto
- **Funciones:**
  - Ver KPIs del proyecto (15 indicadores)
  - Monitorear estado general de reclamos
  - Validar gestión de escombros
  - Control de materiales
  - Ver disponibilidad de técnicos
  - Exportar reportes

### 2.4 ADMINISTRADOR
- **Acceso:** Django admin
- **Funciones:**
  - Gestión completa de datos
  - Creación de usuarios
  - Configuración de constructoras
  - Gestión de especialidades

---

## 3. FLUJOS PRINCIPALES

### 3.1 FLUJO DE RECLAMO (Ciclo Principal)
```
PROPIETARIO CREA RECLAMO
    ↓
Estado: "pendiente"
    ↓
SUPERVISOR ASIGNA TÉCNICO
    ↓
Estado: "asignado"
    ↓
TÉCNICO RECIBE NOTIFICACIÓN
    ↓
TÉCNICO PROGRAMA CITA
    ↓
Estado: "en_proceso"
    ↓
TÉCNICO REALIZA TRABAJO
    ↓
REGISTRA EVIDENCIA + ESCOMBROS + MATERIALES
    ↓
PROPIETARIO RECIBE ENCUESTA DE SATISFACCIÓN
    ↓
Estado: "resuelto"
    ↓
HISTORIAL REGISTRA TODO
```

### 3.2 FLUJO DE AUTENTICACIÓN

```
LOGIN
  ├─ Supervisor (email/username) → Dashboard Supervisor
  ├─ Técnico (RUT/email) → Dashboard Técnico
  ├─ Propietario (RUT/email) → Mis Reclamos
  └─ Admin (staff) → Django Admin
```

**3 Backends de Autenticación:**
1. **SupervisorBackend** - Verifica Perfil.rol='supervisor'
2. **TecnicoBackend** - Permite login por RUT limpio
3. **PropietarioBackend** - Crea usuarios automáticamente

---

## 4. MODELO DE DATOS (Relaciones Principales)

### 4.1 Entidades Principales

```
CONSTRUCTORA (1) ──────(n)─── PROYECTO
                              ├─ Supervisor (Perfil.rol='supervisor')
                              ├─ Propietarios
                              ├─ Técnicos
                              └─ Reclamos

PROPIETARIO (1) ──────(n)─── RECLAMO (el cliente abre defectos)
                              ├─ Estado (pendiente→asignado→en_proceso→resuelto)
                              ├─ Cita programada
                              ├─ Técnico asignado
                              ├─ Evidencia fotográfica
                              ├─ Escombros
                              ├─ Materiales usados
                              └─ Encuesta de satisfacción

TECNICO (1) ──────(n)─── CITA (visitas programadas)
                         ├─ Fecha/Hora
                         ├─ Estado (confirmada/cancelada/completada)
                         └─ Bitácora (todas las acciones)

TECNICO ──────(n)─── ESPECIALIDAD (Electricidad, Pintura, etc.)

ESPECIALIDAD ──────(n)─── RECLAMO (categorización de defectos)
```

### 4.2 Modelos Clave

1. **Perfil** - OneToOne con User de Django
   - rol: admin, supervisor, técnico, propietario
   - rut, telefono, direccion
   - proyecto (FK para supervisores)

2. **Reclamo** - Nucleo del sistema
   - cliente (Propietario)
   - proyecto
   - descripcion, categoria
   - estado, fecha_ingreso
   - tecnico_asignado

3. **Cita** - Programación de visitas
   - reclamo, tecnico, cliente
   - fecha_programada, hora_inicio, hora_fin
   - estado, bitacora de cambios

4. **GestionEscombros** - Retiro de residuos
   - tipo_escombro, volumen_m3
   - empresa_retiro, costo
   - fecha_programada_retiro

5. **EncuestaSatisfaccion** - Feedback del cliente
   - puntuacion (1-5)
   - comentarios
   - fecha_respuesta

---

## 5. FLUJO DE DASHBOARDS

### 5.1 SUPERVISOR DASHBOARD

**Encabezado:**
- Nombre, RUT, Rol, Teléfono, Email
- Proyecto asignado, Constructora

**KPIs Visualizados:**
- Reclamos Abiertos (rojo)
- Reclamos Resueltos (verde)
- Con Retraso >7 días (naranja)
- Satisfacción Promedio (teal)

**Eficiencia Operativa:**
- Tasa de Resolución (% reclamos resueltos)
- Estado del Sistema (operativo/alerta)

**Acceso Rápido:**
- Botones a: Reclamos, KPIs, Escombros, Materiales

**Filtros por Estado:**
- Todos, Ingresados, En Proceso, Resueltos

### 5.2 SUPERVISOR KPIs DASHBOARD

**15 Indicadores:**
1. Total Reclamos
2. Reclamos Abiertos
3. Reclamos Resueltos
4. Tasa Resolución (%)
5. Con Retraso
6. Tiempo Promedio Resolución
7. Satisfacción Promedio
8. Encuestas Completadas
9. Escombros Pendientes
10. Materiales Utilizados
11. Costo Total
12. Citas Completadas
13. Tecnicos Activos
14. Especialidades
15. Carga de Trabajo

---

## 6. FUNCIONALIDADES CRÍTICAS

### 6.1 GESTIÓN DE CITAS (HU-SUP-02)
- Crear cita automáticamente al asignar técnico
- Confirmar/reprogramar por ambas partes
- Enviar notificaciones
- Bitácora de cambios
- Historial completo

### 6.2 VALIDACIÓN DE ESCOMBROS (HU-SUP-04)
- Técnico registra tipo, volumen, empresa retiro
- Supervisor valida antes de retiro
- Empresas de retiro registradas en sistema
- Costos asociados

### 6.3 DISPONIBILIDAD DE TÉCNICOS (HU-SUP-07)
- Técnicos registran disponibilidad (próximos 30 días)
- Horarios en franjas (hora_inicio, hora_fin)
- Supervisor visualiza calendario
- Filtrable por técnico/especialidad

### 6.4 ENCUESTAS DE SATISFACCIÓN
- Envío automático después de resolver reclamo
- Escala 1-5 estrellas
- Comentarios abiertos
- Email con link para responder

### 6.5 GESTIÓN DE MATERIALES
- Registro de materiales utilizados en cada trabajo
- Cantidad, costo
- Control de inventario
- Reportes de consumo

---

## 7. TECNOLOGÍA Y STACK

### Backend
- **Framework:** Django 5.2.7
- **BD:** SQLite3 (dev), puede migrar a PostgreSQL
- **ORM:** Django ORM
- **API:** REST (JSON responses)
- **Filtros avanzados:** django-filter 24.3
- **CORS:** django-cors-headers 4.4.0

### Frontend
- **Template Engine:** Django Templates
- **CSS Framework:** Bootstrap 5
- **JS Charts:** Chart.js 3.9.1
- **Icons:** Font Awesome 6
- **Datepicker:** Bootstrap Datepicker

### Librerías Adicionales
- **HTTP Client:** requests 2.32.3
- **Generación de datos:** Faker 25.8.0
- **WSGI Server:** Werkzeug 3.0.1
- **Manejo de fechas:** python-dateutil 2.9.0
- **Excel:** openpyxl 3.1.5
- **PDF:** reportlab 4.4.5
- **Imágenes:** pillow 12.0.0

### Autenticación
- Django Auth System
- Custom Authentication Backends (3 tipos)
- Session-based
- Password hashing con Django

### Email
- SMTP Gmail
- Notificaciones automáticas
- Templates HTML personalizados

---

## 8. URLS Y RUTAS PRINCIPALES

### Públicas (sin login)
- `/` - Login
- `/login/` - Formulario login
- `/logout/` - Cerrar sesión

### Propietario (cliente)
- `/mis-reclamos/` - Lista de reclamos
- `/crear-reclamo/` - Nuevo reclamo
- `/reclamo/<id>/` - Detalle reclamo
- `/mis-citas/` - Citas programadas

### Técnico
- `/tecnico/dashboard/` - Dashboard técnico
- `/tecnico/mis-citas/` - Citas asignadas
- `/tecnico/disponibilidad/` - Gestionar disponibilidad
- `/tecnico/historial/` - Historial de trabajos

### Supervisor
- `/supervisor/dashboard/` - Dashboard principal
- `/supervisor/kpis/` - KPIs detallados
- `/supervisor/reclamos/` - Listar reclamos
- `/supervisor/escombros/` - Gestión escombros
- `/supervisor/materiales/` - Control materiales
- `/supervisor/disponibilidad/` - Disponibilidad técnicos

---

## 9. ESTADO ACTUAL DEL PROYECTO (v0.2)

### ✅ COMPLETADO
- Autenticación de 4 roles
- Creación y seguimiento de reclamos
- Asignación automática de técnicos
- Gestión de citas (crear/confirmar/reprogramar)
- Encuestas de satisfacción
- Dashboard supervisor con KPIs
- Gestión de escombros
- Control de materiales
- Disponibilidad de técnicos
- Dashboard técnico
- Histórico de cambios (bitácora)
- Notificaciones por email

### 🔄 EN DESARROLLO / MEJORAS
- Dashboard visual más avanzado
- Reportes exportables (Excel/PDF)
- Analytics avanzados
- Integración con sistemas externos
- App móvil

### ⚠️ DEUDA TÉCNICA
- Migraciones de BD ordenadas (45 migraciones)
- Algunos campos deprecados en modelos
- Código legacy en views.py (2900+ líneas)
- Necesita refactorizar modelos

---

## 10. INSTANCIAS ACTUALES

### Supervisores
1. **Juan Pérez** - Edificio Apoquindo (RUT: 18.654.123-8)
2. **Daniel Albornoz** - Condominio Parque Riesco (RUT: 12652127-5)
3. **Daniela Villagomez** - Torre SalfaCorp (RUT: 18.654.123-8)

### Constructoras
- SalfaCorp S.A.
- Otras...

### Proyectos
- EDAPOQ-001 (Edificio Apoquindo)
- CPR-001 (Condominio Parque Riesco)
- TSALFA-001 (Torre SalfaCorp)

---

## 11. RECIENTES CAMBIOS (Esta Sesión)

✅ Reorganización del dashboard supervisor
✅ Agregado campo RUT al modelo Perfil
✅ Actualización de datos de supervisores
✅ Mejoría visual con gradientes y colores
✅ Encabezado tipo panel técnico
✅ KPI dashboard con 15 indicadores
✅ Eliminación de funcionalidad de reportes legacy

---

## 12. PRÓXIMOS PASOS RECOMENDADOS

1. **Limpieza de código:** Refactorizar views.py (dividir en múltiples módulos)
2. **Testing:** Agregar unit tests y tests de integración
3. **Documentación API:** OpenAPI/Swagger
4. **Optimización BD:** Índices, queries optimizadas
5. **Escalabilidad:** Plan de migración a PostgreSQL
6. **UX/UI:** Más dashboards visuales, graficos interactivos
7. **Automatización:** Webhooks, cron jobs para notificaciones

---

## 13. DEPENDENCIAS DEL PROYECTO (Actualizado 21/11/2025)

### Versiones Instaladas
```
asgiref==3.10.0
charset-normalizer==3.4.4
certifi==2025.11.12
crispy-bootstrap5==2025.6
Django==5.2.7
django-cors-headers==4.4.0
django-crispy-forms==2.4
django-filter==24.3
et_xmlfile==2.0.0
Faker==25.8.0
idna==3.11
MarkupSafe==3.0.3
openpyxl==3.1.5
pillow==12.0.0
python-dateutil==2.9.0.post0
python-dotenv==1.1.1
reportlab==4.4.5
requests==2.32.3
six==1.17.0
sqlparse==0.5.3
tzdata==2025.2
urllib3==2.5.0
Werkzeug==3.0.1
```

### Propósito de Nuevas Dependencias

- **requests**: Cliente HTTP para APIs externas
- **Faker**: Generación de datos de prueba realistas
- **django-filter**: Filtros avanzados en vistas (ya integrado)
- **django-cors-headers**: Manejo de CORS para APIs
- **python-dateutil**: Utilidades avanzadas para manejo de fechas
- **Werkzeug**: WSGI utilities y validación de requests

---

**Documento actualizado:** 21/11/2025  
**Status:** ✅ Todas las dependencias instaladas correctamente
