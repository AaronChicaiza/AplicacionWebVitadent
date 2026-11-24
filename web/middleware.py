"""Límites por IP para rutas web, acceso y webhook de WhatsApp."""

import time
import hashlib
import logging

from django.core.cache import cache
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect

logger = logging.getLogger("vitadent.security")


class LimiteSolicitudesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR", "desconocida")
        ahora = int(time.time())
        huella_ip = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:24]
        ventanas = [(f"web:{huella_ip}:{ahora // 600}", 300, 600)]
        tipo_ruta = "api" if request.path.startswith("/api/") else "web"
        limite_cabecera = 300
        duracion = 600
        if request.path == "/acceso/ingresar/" and request.method == "POST":
            ventanas.append((f"login:{huella_ip}:{ahora // 900}", 5, 900))
            tipo_ruta, limite_cabecera, duracion = "login", 5, 900
            usuario = request.POST.get("username", "").strip().casefold()
            if usuario:
                huella = hashlib.sha256(usuario.encode("utf-8")).hexdigest()[:24]
                ventanas.append((f"login-user:{huella}:{ahora // 900}", 5, 900))
        if request.path == "/api/whatsapp/webhook/":
            ventanas.append((f"webhook:{huella_ip}:{ahora // 60}", 120, 60))
            tipo_ruta, limite_cabecera, duracion = "webhook", 120, 60

        cuenta_principal = 0
        for clave, limite, duracion in ventanas:
            cache.add(clave, 0, timeout=duracion)
            try:
                cuenta = cache.incr(clave)
            except ValueError:
                cache.set(clave, 1, timeout=duracion)
                cuenta = 1
            if cuenta > limite:
                logger.warning("rate_limit_exceeded route=%s ip_hash=%s", tipo_ruta, huella_ip)
                respuesta = JsonResponse({"error": "Has realizado demasiadas solicitudes. Intenta de nuevo más tarde."}, status=429)
                respuesta["Retry-After"] = str(duracion)
                respuesta["RateLimit-Limit"] = str(limite_cabecera)
                respuesta["RateLimit-Remaining"] = "0"
                respuesta["RateLimit-Reset"] = str(duracion - (ahora % duracion))
                return respuesta
            if clave.startswith(f"web:{huella_ip}:"):
                cuenta_principal = cuenta

        respuesta = self.get_response(request)
        respuesta["RateLimit-Limit"] = str(limite_cabecera)
        respuesta["RateLimit-Remaining"] = str(max(0, limite_cabecera - cuenta_principal))
        respuesta["RateLimit-Reset"] = str(duracion - (ahora % duracion))
        return respuesta


class CabecerasSeguridadMiddleware:
    """Agrega directivas defensivas compatibles con las plantillas locales."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        respuesta["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "object-src 'none'; img-src 'self' data:; font-src 'self' data:; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; script-src 'self'; connect-src 'self'"
        )
        respuesta["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        respuesta["X-Frame-Options"] = "DENY"
        return respuesta


class CambioClaveInicialMiddleware:
    """Impide usar paneles internos con contraseñas temporales."""

    rutas_permitidas = {"/acceso/cambiar-clave/", "/acceso/salir/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        if usuario and usuario.is_authenticated and request.path not in self.rutas_permitidas and not request.path.startswith("/static/"):
            acceso = getattr(usuario, "acceso_personal", None)
            if acceso and acceso.cambio_clave_obligatorio:
                return HttpResponseRedirect("/acceso/cambiar-clave/")
        return self.get_response(request)
