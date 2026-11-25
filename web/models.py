from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.core.exceptions import ValidationError
from uuid import uuid4
from .validaciones import validar_identificacion_ecuador


def validar_duracion_tratamiento(minutos):
    if minutos is None:
        return
    if minutos < 15:
        raise ValidationError("La duración mínima de una cita es de 15 minutos.")
    if minutos % 15:
        raise ValidationError("La duración debe definirse en intervalos de 15 minutos.")


def generar_codigo_cita():
    return uuid4().hex[:10].upper()


class Especialista(models.Model):
    """Profesional del catálogo; la cuenta es opcional hasta habilitar su acceso."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="perfil_especialista",
        null=True,
        blank=True,
    )
    nombre_completo = models.CharField(max_length=120, blank=True, unique=True)
    especialidad = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre_completo"]
        verbose_name = "especialista"
        verbose_name_plural = "especialistas"

    def __str__(self):
        return f"{self.nombre_completo} · {self.especialidad}"


class Sucursal(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=240, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "sucursal"
        verbose_name_plural = "sucursales"

    def __str__(self):
        return self.nombre


class Tratamiento(models.Model):
    nombre = models.CharField(max_length=140, unique=True)
    area = models.CharField(max_length=100)
    duracion_minutos = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[validar_duracion_tratamiento],
        help_text="Mínimo 15 minutos; aumenta en intervalos de 15. Si se deja vacío, la cita usa 30 minutos.",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["area", "nombre"]
        verbose_name = "tratamiento"
        verbose_name_plural = "tratamientos"

    def __str__(self):
        return self.nombre


class HorarioAtencion(models.Model):
    DIAS = [(0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"), (4, "Viernes"), (5, "Sábado"), (6, "Domingo")]
    especialista = models.ForeignKey(Especialista, on_delete=models.PROTECT, related_name="horarios")
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["dia_semana", "hora_inicio"]
        constraints = [models.UniqueConstraint(fields=["especialista", "dia_semana", "hora_inicio"], name="horario_inicio_unico_especialista_dia")]
        verbose_name = "horario de atención"
        verbose_name_plural = "horarios de atención"

    def clean(self):
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError({"hora_fin": "La hora de cierre debe ser posterior a la hora de inicio."})

    def __str__(self):
        return f"{self.especialista} · {self.get_dia_semana_display()} {self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M}"


class Paciente(models.Model):
    nombre_completo = models.CharField(max_length=160)
    identificacion = models.CharField(max_length=13, unique=True, null=True, blank=True, validators=[validar_identificacion_ecuador])
    telefono = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^[0-9+() -]{7,20}$", "Ingresa un teléfono válido.")],
    )
    correo = models.EmailField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre_completo"]
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"

    def __str__(self):
        return f"{self.nombre_completo} · {self.identificacion}"


class Cita(models.Model):
    class Estado(models.TextChoices):
        SOLICITADA = "solicitada", "Solicitada"
        CONFIRMADA = "confirmada", "Confirmada"
        REPROGRAMADA = "reprogramada", "Reprogramada"
        CANCELADA = "cancelada", "Cancelada"
        ATENDIDA = "atendida", "Atendida"

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="citas")
    especialista = models.ForeignKey(
        Especialista,
        on_delete=models.PROTECT,
        related_name="citas",
        null=True,
        blank=True,
    )
    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.PROTECT, related_name="citas")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="citas", null=True, blank=True)
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    fecha_hora_solicitada = models.DateTimeField()
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.SOLICITADA)
    monto_ingreso = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    atendida_en = models.DateTimeField(null=True, blank=True)
    codigo = models.CharField(max_length=12, unique=True, default=generar_codigo_cita)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_hora_solicitada"]
        verbose_name = "cita"
        verbose_name_plural = "citas"

    def __str__(self):
        return f"{self.codigo} · {self.paciente} · {self.fecha_hora_solicitada:%d/%m/%Y %H:%M}"


class Conversacion(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "activa", "Activa"
        HUMANA = "humana", "Requiere atención humana"
        CERRADA = "cerrada", "Cerrada"

    canal = models.CharField(max_length=20, default="whatsapp")
    identificador_hash = models.CharField(max_length=64, unique=True)
    whatsapp_id = models.CharField(max_length=20)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVA)
    iniciada_en = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ultima_actividad"]
        verbose_name = "conversación"
        verbose_name_plural = "conversaciones"

    def __str__(self):
        return f"WhatsApp · {self.identificador_hash[:10]} · {self.get_estado_display()}"


class MensajeConversacion(models.Model):
    class Direccion(models.TextChoices):
        ENTRANTE = "entrante", "Entrante"
        SALIENTE = "saliente", "Saliente"

    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name="mensajes")
    identificador_proveedor = models.CharField(max_length=180, unique=True, null=True, blank=True)
    direccion = models.CharField(max_length=10, choices=Direccion.choices)
    tipo = models.CharField(max_length=24, default="text")
    contenido = models.TextField(max_length=4000, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en"]
        verbose_name = "mensaje de conversación"
        verbose_name_plural = "mensajes de conversación"


class EventoAuditoria(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=64)
    tipo_objeto = models.CharField(max_length=64, blank=True)
    identificador_objeto = models.CharField(max_length=64, blank=True)
    detalles = models.JSONField(default=dict, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["accion", "creado_en"])]
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"


class Notificacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ENVIADA = "enviada", "Enviada"
        FALLIDA = "fallida", "Fallida"

    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name="notificaciones")
    canal = models.CharField(max_length=20, default="whatsapp")
    tipo = models.CharField(max_length=32)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    programada_para = models.DateTimeField()
    enviada_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["programada_para"]
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"


class CitaEvento(models.Model):
    class Accion(models.TextChoices):
        SOLICITADA = "solicitada", "Solicitud creada"
        ASIGNADA = "asignada", "Especialista asignado"
        CONFIRMADA = "confirmada", "Cita confirmada"
        ATENDIDA = "atendida", "Atendida"
        CANCELADA = "cancelada", "Cita cancelada"
        REPROGRAMADA = "reprogramada", "Cita reprogramada"

    cita = models.ForeignKey(Cita, on_delete=models.PROTECT, related_name="eventos")
    accion = models.CharField(max_length=16, choices=Accion.choices)
    fecha_anterior = models.DateTimeField(null=True, blank=True)
    fecha_nueva = models.DateTimeField(null=True, blank=True)
    motivo = models.CharField(max_length=300, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "evento de cita"
        verbose_name_plural = "eventos de citas"

    def __str__(self):
        return f"{self.get_accion_display()} · {self.cita.codigo} · {self.creado_en:%d/%m/%Y %H:%M}"


class AccesoPersonal(models.Model):
    """Controla requisitos de acceso propios del personal VitaDent."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="acceso_personal",
    )
    cambio_clave_obligatorio = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "acceso de personal"
        verbose_name_plural = "accesos de personal"

    def __str__(self):
        return f"{self.usuario.username} · {'cambiar clave' if self.cambio_clave_obligatorio else 'activo'}"
