"""Serializadores de entrada y salida de la API pública e interna."""

import re
import hashlib
import json
from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import Cita, Conversacion, Especialista, MensajeConversacion, Paciente, Sucursal, Tratamiento
from .validaciones import validar_identificacion_ecuador


class TratamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tratamiento
        fields = ("id", "nombre", "area", "duracion_minutos")


class EspecialistaPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialista
        fields = ("id", "nombre_completo", "especialidad")


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ("id", "nombre", "direccion")


class SolicitudWhatsAppSerializer(serializers.Serializer):
    nombre = serializers.CharField(min_length=3, max_length=80, trim_whitespace=True)
    identificacion = serializers.CharField(min_length=10, max_length=13, trim_whitespace=True)
    telefono = serializers.RegexField(r"^\+?[0-9]{7,15}$", max_length=16)
    correo = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    tratamiento = serializers.CharField(max_length=140, trim_whitespace=True)
    especialista = serializers.CharField(max_length=120, required=False, allow_blank=True, trim_whitespace=True)
    fecha_hora = serializers.DateTimeField()
    sucursal = serializers.CharField(max_length=100, required=False, allow_blank=True, trim_whitespace=True)
    idempotency_key = serializers.RegexField(r"^[a-f0-9]{64}$", required=False, max_length=64)

    def validate_nombre(self, value):
        value = re.sub(r"\s+", " ", value).strip()
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'-]{1,78}", value):
            raise serializers.ValidationError("Escribe tu nombre y apellido usando solo letras.")
        return value

    def validate_identificacion(self, value):
        try:
            validar_identificacion_ecuador(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages[0]) from error
        return re.sub(r"\D", "", value)

    def validate_fecha_hora(self, value):
        if value <= timezone.now() or value > timezone.now() + timedelta(days=365):
            raise serializers.ValidationError("La fecha debe ser futura y estar dentro de los próximos 12 meses.")
        return value

    def validate(self, attrs):
        tratamiento = Tratamiento.objects.filter(nombre__iexact=attrs["tratamiento"], activo=True).first()
        if not tratamiento:
            raise serializers.ValidationError({"tratamiento": "El tratamiento no está en el catálogo activo."})
        attrs["tratamiento_obj"] = tratamiento
        especialista_nombre = attrs.get("especialista", "")
        if especialista_nombre and especialista_nombre.casefold() not in {"cualquiera", "por asignar"}:
            especialista = Especialista.objects.filter(nombre_completo__iexact=especialista_nombre, activo=True).first()
            if not especialista:
                raise serializers.ValidationError({"especialista": "El especialista no está en el catálogo activo."})
            attrs["especialista_obj"] = especialista
        else:
            attrs["especialista_obj"] = None
        sucursal_nombre = attrs.get("sucursal", "")
        if sucursal_nombre:
            sucursal = Sucursal.objects.filter(nombre__iexact=sucursal_nombre, activa=True).first()
            if not sucursal:
                raise serializers.ValidationError({"sucursal": "La sucursal no está en el catálogo activo."})
            attrs["sucursal_obj"] = sucursal
        else:
            sucursales = list(Sucursal.objects.filter(activa=True)[:2])
            if len(sucursales) > 1:
                raise serializers.ValidationError({"sucursal": "Indica la sucursal para continuar."})
            attrs["sucursal_obj"] = sucursales[0] if sucursales else None
        if not attrs.get("idempotency_key"):
            base = json.dumps({k: str(v) for k, v in attrs.items() if not k.endswith("_obj")}, sort_keys=True, ensure_ascii=False)
            attrs["idempotency_key"] = hashlib.sha256(base.encode("utf-8")).hexdigest()
        return attrs


class OperacionCitaWhatsAppSerializer(serializers.Serializer):
    codigo = serializers.RegexField(r"^[A-Za-z0-9]{6,12}$", max_length=12)
    identificacion = serializers.CharField(min_length=10, max_length=13, trim_whitespace=True)
    telefono = serializers.RegexField(r"^[0-9]{7,15}$", max_length=15)
    nueva_fecha_hora = serializers.DateTimeField(required=False)
    motivo = serializers.CharField(max_length=300, required=False, allow_blank=True, trim_whitespace=True)

    def validate_identificacion(self, value):
        try:
            validar_identificacion_ecuador(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError("Los datos de validación no coinciden.") from error
        return re.sub(r"\D", "", value)

    def validate_nueva_fecha_hora(self, value):
        if value <= timezone.now() or value > timezone.now() + timedelta(days=365):
            raise serializers.ValidationError("La nueva fecha debe ser futura y estar dentro de los próximos 12 meses.")
        return value


class CitaLecturaSerializer(serializers.ModelSerializer):
    paciente = serializers.CharField(source="paciente.nombre_completo", read_only=True)
    tratamiento = serializers.CharField(source="tratamiento.nombre", read_only=True)
    especialista = serializers.CharField(source="especialista.nombre_completo", read_only=True, allow_null=True)
    sucursal = serializers.CharField(source="sucursal.nombre", read_only=True, allow_null=True)

    class Meta:
        model = Cita
        fields = ("id", "codigo", "paciente", "tratamiento", "especialista", "sucursal", "fecha_hora_solicitada", "estado", "creado_en")
        read_only_fields = fields


class CambioEstadoCitaSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Cita.Estado.choices)
    motivo = serializers.CharField(max_length=300, required=False, allow_blank=True, trim_whitespace=True)


class PacienteLecturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = ("id", "nombre_completo", "identificacion", "telefono", "correo", "creado_en")
        read_only_fields = fields


class BloqueDisponibleSerializer(serializers.Serializer):
    inicio = serializers.DateTimeField()
    fin = serializers.DateTimeField()


class DisponibilidadRespuestaSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    especialista = serializers.IntegerField()
    duracion_minutos = serializers.IntegerField()
    bloques = BloqueDisponibleSerializer(many=True)


class ConversacionResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversacion
        fields = ("id", "canal", "whatsapp_id", "estado", "iniciada_en", "ultima_actividad")
        read_only_fields = fields


class MensajeConversacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensajeConversacion
        fields = ("id", "direccion", "tipo", "contenido", "creado_en")
        read_only_fields = fields


class EstadoConversacionSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Conversacion.Estado.choices)
