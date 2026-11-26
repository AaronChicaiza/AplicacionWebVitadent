import re

from django.core.exceptions import ValidationError


def validar_identificacion_ecuador(valor):
    """Valida cédula ecuatoriana de 10 dígitos o RUC de persona natural."""
    entrada = str(valor or "").strip()
    if not re.fullmatch(r"[0-9 .-]+", entrada):
        raise ValidationError("La identificación solo admite dígitos y separadores simples.")
    digitos = re.sub(r"\D", "", entrada)
    if len(digitos) not in (10, 13):
        raise ValidationError("La identificación debe tener 10 dígitos o 13 dígitos de RUC.")
    cedula = digitos[:10]
    provincia = int(cedula[:2])
    if not 1 <= provincia <= 24 or int(cedula[2]) >= 6:
        raise ValidationError("La identificación no corresponde al formato ecuatoriano.")
    total = 0
    for indice, caracter in enumerate(cedula[:9]):
        producto = int(caracter) * (2 if indice % 2 == 0 else 1)
        total += producto - 9 if producto >= 10 else producto
    verificador = (10 - total % 10) % 10
    if verificador != int(cedula[9]):
        raise ValidationError("El dígito verificador de la identificación no es válido.")
    if len(digitos) == 13 and digitos[10:] == "000":
        raise ValidationError("El RUC no tiene un establecimiento válido.")


