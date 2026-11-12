import json
import logging
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)
visual_lock = Lock()
chat_lock = Lock()


@lru_cache(maxsize=1)
def visual():
    from predictor import Predictor
    return Predictor()


@lru_cache(maxsize=1)
def conversacion():
    from .conversacion import AFUModelService
    return AFUModelService()


def inicio(request):
    return render(request, "inicio.html", {"animal": request.session.get("animal")})


def error(mensaje, estado):
    return JsonResponse({"success": False, "mensaje": mensaje}, status=estado)


@require_POST
def identificar(request):
    archivo = request.FILES.get("imagen")
    if not archivo or archivo.size > 10 * 1024 * 1024:
        return error("Selecciona una imagen de hasta 10 MB.", 400)
    try:
        with Image.open(archivo) as imagen:
            if imagen.width * imagen.height > 25000000:
                return error("La imagen supera los 25 megapíxeles.", 400)
            imagen.verify()
    except (OSError, ValueError, Image.DecompressionBombError, UnidentifiedImageError):
        return error("No se pudo leer la fotografía.", 400)
    try:
        archivo.seek(0)
        with TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "foto"
            with ruta.open("wb") as destino:
                for bloque in archivo.chunks():
                    destino.write(bloque)
            with visual_lock:
                resultado = visual().predecir(str(ruta))
    except Exception:
        logger.exception("Error del clasificador")
        return error("No se pudo analizar la imagen. Revisa la consola del servidor.", 503)
    animal = {"nombre": resultado["animal"], "confianza_clasificador": resultado["confianza"]}
    request.session["animal"] = animal
    return JsonResponse({"success": True, "animal": animal, "confianza": resultado["confianza"],
                         "mensaje": f"{animal['nombre']} · Confianza del clasificador: {resultado['confianza']:.2f} %"})


@require_POST
def preguntar(request):
    animal = request.session.get("animal")
    if not animal:
        return error("Primero identifica un animal.", 400)
    try:
        datos = json.loads(request.body)
    except (ValueError, UnicodeError):
        return error("El mensaje debe enviarse en JSON.", 400)
    mensaje = datos.get("mensaje") if isinstance(datos, dict) else None
    if not isinstance(mensaje, str) or not 1 <= len(mensaje.strip()) <= 2000:
        return error("Escribe una pregunta de hasta 2000 caracteres.", 400)
    try:
        with chat_lock:
            respuesta = conversacion().preguntar(mensaje.strip(), animal)
    except Exception:
        logger.exception("Error del modelo conversacional")
        return error("AFU no pudo responder. Comprueba CUDA y la disponibilidad de Qwen en la consola.", 503)
    return JsonResponse({"success": True, "respuesta": respuesta})
