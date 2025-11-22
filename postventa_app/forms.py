from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Reclamo, ArchivoEvidencia, Propietario, Proyecto, Tecnico, Cita, Unidad, Especialidad, Categoria


# ========================================
# FORMULARIOS DE AUTENTICACIÓN
# ========================================

class RegistroClienteForm(UserCreationForm):
    """Formulario de registro para nuevos clientes/propietarios"""
    
    # Campos del User
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.cl'
        })
    )
    
    # Campos del Cliente
    rut = forms.CharField(
        max_length=12,
        required=True,
        label='RUT',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12.345.678-9'
        })
    )
    
    nombre = forms.CharField(
        max_length=100,
        required=True,
        label='Nombre Completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Juan Pérez González'
        })
    )
    
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+56 9 1234 5678'
        })
    )
    
    direccion = forms.CharField(
        max_length=200,
        required=False,
        label='Dirección',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Calle 123, Comuna'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuario'
            })
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if Propietario.objects.filter(rut=rut).exists():
            raise forms.ValidationError('Ya existe un cliente con este RUT.')
        return rut

    def save(self, commit=True):
        """Crear User y Propietario vinculados"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Crear el Propietario asociado
            Propietario.objects.create(
                user=user,
                nombre=self.cleaned_data['nombre'],
                rut=self.cleaned_data['rut'],
                email=self.cleaned_data['email'],
                telefono=self.cleaned_data.get('telefono', ''),
                direccion=self.cleaned_data.get('direccion', ''),
                estado='activo'
            )
        return user



# ========================================
# FORMULARIOS DE RECLAMO
# ========================================

class ReclamoForm(forms.ModelForm):
    descripcion = forms.CharField(
        required=True,
        label='Descripción',
        min_length=20,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa detalladamente el problema',
            'required': 'required',
            'minlength': '20',
        }),
        error_messages={
            'required': 'Este campo es obligatorio.',
            'min_length': 'Debe ingresar al menos 20 caracteres.'
        }
    )
    """Formulario para crear/editar reclamos"""
    PRIORIDAD_CHOICES = [
        ('', 'Seleccione una prioridad'),
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    def __init__(self, *args, **kwargs):
        cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].widget.attrs.update({
            'required': 'required',
            'minlength': '20',
        })
        if cliente:
            self.fields['unidad'].queryset = cliente.unidades.all()
            proyectos_cliente = set(u.proyecto for u in cliente.unidades.all())
            self.fields['proyecto'].queryset = Proyecto.objects.filter(id_proyecto__in=[p.id_proyecto for p in proyectos_cliente])
            if len(proyectos_cliente) == 1:
                self.fields['proyecto'].initial = list(proyectos_cliente)[0]
        else:
            self.fields['unidad'].queryset = Unidad.objects.none()
            self.fields['proyecto'].queryset = Proyecto.objects.none()

    categoria = forms.ModelChoiceField(
        queryset=Especialidad.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Categoría',
        error_messages={'required': 'Debe seleccionar una categoría'}
    )
    prioridad = forms.ChoiceField(
        choices=PRIORIDAD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    unidad = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Unidad'
    )
    proyecto = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Proyecto'
    )

    class Meta:
        model = Reclamo
        fields = ['descripcion', 'categoria', 'unidad', 'prioridad', 'proyecto']
        widgets = {
            'proyecto': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'unidad': 'Unidad',
            'prioridad': 'Prioridad',
            'proyecto': 'Proyecto'
        }


class ReclamoSimpleForm(forms.ModelForm):
    """Formulario simplificado para crear reclamos"""
    
    class Meta:
        model = Reclamo
        fields = ['descripcion', 'categoria']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describa el problema'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo de problema'
            })
        }


class ArchivoEvidenciaForm(forms.ModelForm):
    """Formulario para subir archivos de evidencia"""
    
    class Meta:
        model = ArchivoEvidencia
        fields = ['archivo', 'tipo', 'descripcion']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*,.pdf'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción del archivo (opcional)'
            })
        }


# ========================================
# FORMULARIOS DE CITA
# ========================================

class CitaForm(forms.ModelForm):
    """Formulario para agendar citas"""
    
    class Meta:
        model = Cita
        fields = ['fecha_programada', 'tipo_cita', 'duracion_estimada_minutos']
        widgets = {
            'fecha_programada': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'tipo_cita': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo de visita'
            }),
            'duracion_estimada_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '30',
                'step': '30',
                'value': '120'
            })
        }
        labels = {
            'fecha_programada': 'Fecha y Hora',
            'tipo_cita': 'Tipo de Cita',
            'duracion_estimada_minutos': 'Duración Estimada (minutos)'
        }


# Mantener compatibilidad con código antiguo
RegistroPropietarioForm = RegistroClienteForm  # Alias
ReclamoAutenticadoForm = ReclamoForm  # Alias
from django.forms import inlineformset_factory
ImagenReclamoFormSet = inlineformset_factory(
    Reclamo,
    ArchivoEvidencia,
    fields=['archivo', 'tipo', 'descripcion'],
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    widgets={
        'archivo': forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*,.pdf'
        }),
        'tipo': forms.HiddenInput(),  # Campo oculto, se rellenará con JS
        'descripcion': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción opcional'
        })
    },
    labels={
        'archivo': 'Archivo',
        'tipo': '',
        'descripcion': 'Descripción'
    },
    help_texts={
        'archivo': '',
        'tipo': '',
        'descripcion': ''
    }
)
