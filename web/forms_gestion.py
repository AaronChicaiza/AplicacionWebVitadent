"""Formularios del panel de gestión VitaDent.

Las validaciones se ejecutan en el servidor con Django ModelForms; la tabla
solo controla la presentación y nunca sustituye estas comprobaciones.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Q, Value, When

from .datos_demo import ORDEN_AREAS_TRATAMIENTO, ORDEN_PARES_TRATAMIENTO
from .models import Especialista, HorarioAtencion, Paciente, Sucursal, Tratamiento, Cita
from .validaciones import especialidad_admite_tratamiento


class EspecialistaGestionForm(forms.ModelForm):
    class Meta:
        model = Especialista
        fields = ("nombre_completo", "especialidad", "usuario", "activo")
        labels = {
            "nombre_completo": "Nombre del especialista",
            "especialidad": "Especialidad",
            "usuario": "Cuenta profesional (opcional)",
            "activo": "Disponible en el catálogo",
        }
        widgets = {
            "nombre_completo": forms.TextInput(attrs={"maxlength": 120, "autocomplete": "name"}),
            "especialidad": forms.TextInput(attrs={"maxlength": 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        usuario = get_user_model()
        candidatos = usuario.objects.filter(is_active=True, is_staff=False)
        if self.instance.pk:
            candidatos = candidatos.filter(Q(perfil_especialista__isnull=True) | Q(perfil_especialista=self.instance))
        else:
            candidatos = candidatos.filter(perfil_especialista__isnull=True)
        candidatos = candidatos.order_by("username")
        self.fields["usuario"].queryset = candidatos
        self.fields["usuario"].required = False
        self.fields["usuario"].empty_label = "Sin cuenta vinculada"


class TratamientoGestionForm(forms.ModelForm):
    area = forms.ChoiceField(choices=[(area, area) for area in ORDEN_AREAS_TRATAMIENTO], label="Área o especialidad")

    class Meta:
        model = Tratamiento
        fields = ("nombre", "area", "duracion_minutos", "activo")
        labels = {
            "nombre": "Tratamiento",
            "area": "Área o especialidad",
            "duracion_minutos": "Duración de la cita (minutos)",
            "activo": "Disponible en el catálogo",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"maxlength": 140}),
            "duracion_minutos": forms.NumberInput(attrs={"min": 15, "max": 32760, "step": 15}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        area_actual = getattr(self.instance, "area", "")
        if area_actual and area_actual not in ORDEN_AREAS_TRATAMIENTO:
            self.fields["area"].choices = [*self.fields["area"].choices, (area_actual, f"{area_actual} (inactiva)")]


class PacienteGestionForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ("nombre_completo", "identificacion", "telefono", "correo")
        labels = {
            "nombre_completo": "Nombre completo",
            "identificacion": "Identificación",
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
        }
        widgets = {
            "nombre_completo": forms.TextInput(attrs={"maxlength": 160, "autocomplete": "name"}),
            "identificacion": forms.TextInput(attrs={"maxlength": 13, "inputmode": "numeric"}),
            "telefono": forms.TextInput(attrs={"maxlength": 20, "autocomplete": "tel"}),
            "correo": forms.EmailInput(attrs={"maxlength": 254, "autocomplete": "email"}),
        }

    def clean_identificacion(self):
        return self.cleaned_data.get("identificacion") or None


class SelectorHoraWidget(forms.MultiWidget):
    """Selector simple de hora y minutos en dos listas cortas."""

    def __init__(self, attrs=None):
        horas = [('', 'Hora')] + [(f'{hora:02d}', f'{hora:02d}') for hora in range(24)]
        minutos = [('', 'Minutos')] + [(f'{minuto:02d}', f'{minuto:02d}') for minuto in range(60)]
        widgets = (
            forms.Select(choices=horas, attrs={'aria-label': 'Hora'}),
            forms.Select(choices=minutos, attrs={'aria-label': 'Minutos'}),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            if isinstance(value, str):
                value = forms.TimeField().to_python(value)
            return [f'{value.hour:02d}', f'{value.minute:02d}']
        return ['', '']

    def value_from_datadict(self, data, files, name):
        hora = data.get(f'{name}_0', '')
        minuto = data.get(f'{name}_1', '')
        return f'{hora}:{minuto}' if hora and minuto else ''


class HorarioGestionForm(forms.ModelForm):
    class Meta:
        model = HorarioAtencion
        fields = ("especialista", "dia_semana", "hora_inicio", "hora_fin", "activo")
        labels = {
            "especialista": "Especialista",
            "dia_semana": "Día",
            "hora_inicio": "Hora de inicio",
            "hora_fin": "Hora de fin",
            "activo": "Horario activo",
        }
        help_texts = {
            "hora_inicio": "Elige la hora y los minutos por separado (formato de 24 horas).",
            "hora_fin": "Elige la hora y los minutos por separado (formato de 24 horas).",
        }
        widgets = {
            "hora_inicio": SelectorHoraWidget(),
            "hora_fin": SelectorHoraWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["especialista"].queryset = Especialista.objects.order_by("nombre_completo")


class SucursalGestionForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ("nombre", "direccion", "telefono", "activa")
        labels = {
            "nombre": "Nombre de la sucursal",
            "direccion": "Dirección",
            "telefono": "Teléfono",
            "activa": "Sucursal activa",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"maxlength": 100}),
            "direccion": forms.TextInput(attrs={"maxlength": 240}),
            "telefono": forms.TextInput(attrs={"maxlength": 20}),
        }


class CitaGestionForm(forms.ModelForm):
    fecha_hora_solicitada = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
        label="Fecha y hora",
    )

    class Meta:
        model = Cita
        fields = ("paciente", "tratamiento", "especialista", "sucursal", "fecha_hora_solicitada")
        labels = {
            "paciente": "Paciente",
            "tratamiento": "Tratamiento",
            "especialista": "Especialista",
            "sucursal": "Sucursal",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orden_catalogo = Case(*[When(nombre=nombre, area=area, then=Value(indice)) for indice, (nombre, area) in enumerate(ORDEN_PARES_TRATAMIENTO)], default=Value(len(ORDEN_PARES_TRATAMIENTO)), output_field=IntegerField())
        self.fields["tratamiento"].queryset = Tratamiento.objects.filter(activo=True).order_by(orden_catalogo)
        self.fields["especialista"].queryset = Especialista.objects.filter(activo=True).order_by("nombre_completo")
        self.fields["sucursal"].queryset = Sucursal.objects.filter(activa=True).order_by("nombre")
        self.fields["especialista"].required = False
        self.fields["sucursal"].required = False

    def clean(self):
        datos = super().clean()
        tratamiento = datos.get("tratamiento")
        especialista = datos.get("especialista")
        fecha = datos.get("fecha_hora_solicitada")
        if tratamiento and especialista and not especialidad_admite_tratamiento(tratamiento.area, especialista.especialidad):
            self.add_error("especialista", "Este especialista no corresponde al área del tratamiento.")
        if fecha:
            from django.utils import timezone
            if fecha <= timezone.now():
                self.add_error("fecha_hora_solicitada", "Selecciona una fecha futura.")
        return datos
