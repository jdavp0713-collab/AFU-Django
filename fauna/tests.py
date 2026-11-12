from io import BytesIO
from unittest.mock import patch
from django.test import TestCase, Client
from PIL import Image


class SesionesTest(TestCase):
    def test_el_chat_recibe_el_animal_del_navegador(self):
        foto = BytesIO()
        Image.new("RGB", (20, 20)).save(foto, "PNG")
        foto.seek(0)
        foto.name = "foto.png"
        with patch("fauna.views.visual") as modelo:
            modelo.return_value.predecir.return_value = {"animal": "Mapache", "confianza": 96.2}
            self.assertTrue(self.client.post("/api/predict", {"imagen": foto}).json()["success"])
        with patch("fauna.views.conversacion") as servicio:
            servicio.return_value.preguntar.return_value = "Respuesta de prueba"
            datos = {"mensaje": "¿Qué come?"}
            self.assertEqual(self.client.post("/api/chat", datos, content_type="application/json").status_code, 200)
            servicio.return_value.preguntar.assert_called_once_with("¿Qué come?", {"nombre": "Mapache", "confianza_clasificador": 96.2})
            self.assertEqual(Client().post("/api/chat", datos, content_type="application/json").status_code, 400)
