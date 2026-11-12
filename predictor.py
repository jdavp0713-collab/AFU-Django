import os
import json
import cv2
import numpy as np
import tensorflow as tf


# ==========================
# RUTAS ABSOLUTAS
# ==========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELO_PATH = os.path.join(
    BASE_DIR,
    "modelo_animales_final_v3.keras"
)

CLASES_PATH = os.path.join(
    BASE_DIR,
    "clases.json"
)


class Predictor:

    def __init__(self):

        self.img_size = (224, 224)

        print("=" * 60)
        print("Inicializando Predictor AFU...")
        print("=" * 60)

        print(f"Modelo: {MODELO_PATH}")
        print(f"Clases: {CLASES_PATH}")

        if not os.path.exists(MODELO_PATH):
            raise FileNotFoundError(
                f"No se encontró el modelo:\n{MODELO_PATH}"
            )

        if not os.path.exists(CLASES_PATH):
            raise FileNotFoundError(
                f"No se encontró clases.json:\n{CLASES_PATH}"
            )

        # ==========================
        # CARGAR MODELO
        # ==========================

        print("\nCargando modelo visual...")

        self.modelo = tf.keras.models.load_model(
            MODELO_PATH, compile=False
        )

        print("✅ Modelo cargado correctamente.")

        # ==========================
        # CARGAR CLASES
        # ==========================

        with open(
            CLASES_PATH,
            "r",
            encoding="utf-8"
        ) as archivo:

            self.clases = json.load(archivo)

        print("✅ Clases cargadas correctamente.")

        # ==========================
        # VERIFICACIONES
        # ==========================

        num_salidas = self.modelo.output_shape[-1]
        num_clases = len(self.clases)

        print()
        print("Salida del modelo:", self.modelo.output_shape)
        print("Número de clases:", num_clases)

        if num_salidas != num_clases:
            raise ValueError(
                f"El modelo tiene {num_salidas} salidas, "
                f"pero clases.json contiene {num_clases} clases."
            )

        print("✅ Modelo y clases son compatibles.")
        print("=" * 60)


    def predecir(self, ruta_imagen):

        if not os.path.exists(ruta_imagen):
            raise FileNotFoundError(
                f"No existe la imagen:\n{ruta_imagen}"
            )

        imagen = cv2.imread(ruta_imagen)

        if imagen is None:
            raise Exception(
                "No se pudo leer la imagen."
            )

        # OpenCV usa BGR
        # El modelo fue entrenado con imágenes RGB
        imagen = cv2.cvtColor(
            imagen,
            cv2.COLOR_BGR2RGB
        )

        # Redimensionar al tamaño utilizado
        # durante el entrenamiento
        imagen = cv2.resize(
            imagen,
            self.img_size
        )

        imagen = imagen.astype(
            np.float32
        )

        # Crear batch:
        # (224,224,3) -> (1,224,224,3)
        imagen = np.expand_dims(
            imagen,
            axis=0
        )

        # ==========================
        # PREDICCIÓN
        # ==========================

        predicciones = self.modelo.predict(
            imagen,
            verbose=0
        )[0]

        indice = int(
            np.argmax(predicciones)
        )

        confianza = float(
            predicciones[indice] * 100
        )

        animal = self.clases[
            str(indice)
        ]

        return {
            "animal": animal,
            "confianza": round(
                confianza,
                2
            )
        }


# ==========================
