"""Formularios del panel de gestión VitaDent.

Las validaciones se ejecutan en el servidor con Django ModelForms; la tabla
solo controla la presentación y nunca sustituye estas comprobaciones.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Q, Value, When

from .datos_demo import ORDEN_AREAS_TRATAMIENTO, ORDEN_PARES_TRATAMIENTO
from .models import Especialista, HorarioAtencion, Paciente, Sucursal, Tratamiento, Cita


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
        fields = ("nombre_completo", "identificacion", "telefono", "correo", "nota")
        labels = {
            "nombre_completo": "Nombre completo",
            "identificacion": "Identificación",
            "telefono": "Teléfono",
            "correo": "Correo electrónico",
            "nota": "Nota interna",
        }
        widgets = {
            "nombre_completo": forms.TextInput(attrs={"maxlength": 160, "autocomplete": "name"}),
            "identificacion": forms.TextInput(attrs={"maxlength": 13, "inputmode": "numeric"}),
            "telefono": forms.TextInput(attrs={"maxlength": 20, "autocomplete": "tel"}),
            "correo": forms.EmailInput(attrs={"maxlength": 254, "autocomplete": "email"}),
            "nota": forms.Textarea(attrs={"maxlength": 1000, "rows": 3}),
        }

    def clean_identificacion(self):
        return self.cleaned_data.get("identificacion") or None


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
            "hora_inicio": forms.TimeInput(format="%H:%M", attrs={"type": "text", "class": "admin-time-input", "placeholder": "HH:MM", "inputmode": "numeric", "list": "horarios-sugeridos", "pattern": "(?:[01][0-9]|2[0-3]):[0-5][0-9]"}),
            "hora_fin": forms.TimeInput(format="%H:%M", attrs={"type": "text", "class": "admin-time-input", "placeholder": "HH:MM", "inputmode": "numeric", "list": "horarios-sugeridos", "pattern": "(?:[01][0-9]|2[0-3]):[0-5][0-9]"}),
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
        fields = ("paciente", "tratamiento", "especialista", "sucursal", "fecha_hora_solicitada", "comentario", "monto_total", "monto_ingreso")
        labels = {
            "paciente": "Paciente",
            "tratamiento": "Tratamiento",
            "especialista": "Especialista",
            "sucursal": "Sucursal",
            "comentario": "Nota de la cita",
            "monto_total": "Total acordado (USD)",
            "monto_ingreso": "Pagado hasta ahora (USD)",
        }
        widgets = {
            "comentario": forms.Textarea(attrs={"rows": 3, "maxlength": 1000}),
            "monto_total": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "0.00"}),
            "monto_ingreso": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "0.00"}),
        }
        help_texts = {
            "monto_total": "Importe acordado para esta cita. Déjalo vacío si aún no se conoce.",
            "monto_ingreso": "Suma efectivamente recibida. El saldo se calcula automáticamente.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orden_catalogo = Case(*[When(nombre=nombre, area=area, then=Value(indice)) for indice, (nombre, area) in enumerate(ORDEN_PARES_TRATAMIENTO)], default=Value(len(ORDEN_PARES_TRATAMIENTO)), output_field=IntegerField())
        self.fields["tratamiento"].queryset = Tratamiento.objects.filter(Q(activo=True) | Q(pk=self.instance.tratamiento_id)).order_by(orden_catalogo)
        self.fields["especialista"].queryset = Especialista.objects.filter(Q(activo=True) | Q(pk=self.instance.especialista_id)).order_by("nombre_completo")
        self.fields["sucursal"].queryset = Sucursal.objects.filter(Q(activa=True) | Q(pk=self.instance.sucursal_id)).order_by("nombre")
        self.fields["especialista"].required = False
        self.fields["sucursal"].required = False

    def clean(self):
        datos = super().clean()
        fecha = datos.get("fecha_hora_solicitada")
        if fecha:
            from django.utils import timezone
            fecha_cambio = not self.instance.pk or fecha.replace(second=0, microsecond=0) != self.instance.fecha_hora_solicitada.replace(second=0, microsecond=0)
            if fecha <= timezone.now() and fecha_cambio and self.instance.estado != Cita.Estado.ATENDIDA:
                self.add_error("fecha_hora_solicitada", "Selecciona una fecha futura.")
        total = datos.get("monto_total")
        pagado = datos.get("monto_ingreso")
        if total is not None and total < 0:
            self.add_error("monto_total", "El total no puede ser negativo.")
        if pagado is not None and pagado < 0:
            self.add_error("monto_ingreso", "Lo pagado no puede ser negativo.")
        if pagado is not None and total is None:
            self.add_error("monto_total", "Indica el total acordado para calcular el saldo.")
        elif total is not None and pagado is not None and pagado > total:
            self.add_error("monto_ingreso", "Lo pagado no puede superar el total acordado.")
        return datos
