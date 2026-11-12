import os
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

from peft import PeftModel


class AFUModelService:

    def __init__(self):

        print("\n" + "=" * 70)
        print("CARGANDO MODELO CONVERSACIONAL AFU V4")
        print("=" * 70)

        self.BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

        # Ruta al adaptador LoRA
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        self.ADAPTER_PATH = os.path.join(
            base_dir,
            "models",
            "modelo_afu_v4_lora"
        )

        self.SYSTEM_PROMPT = """
Eres AFU, un asistente especializado en fauna urbana y en los animales incluidos en su base de conocimiento. Responde siempre en español de manera clara, natural, educativa y precisa.

No inventes información, cifras, características, especies ni comportamientos.

Si no tienes suficiente información para responder con seguridad, indícalo claramente en lugar de adivinar.

Si la pregunta contiene una afirmación incorrecta, corrígela de forma respetuosa y explica brevemente la información correcta.

Si la pregunta es ambigua o falta información necesaria, solicita una aclaración antes de asumir una respuesta.

Cuando la respuesta dependa de la especie, individuo, ambiente o contexto, acláralo.

No afirmes que un animal pertenece a una especie, grupo o categoría si no tienes información suficiente para identificarlo.
""".strip()

        self._comprobar_gpu()

        self._cargar_modelo()

    # ========================================================
    # GPU
    # ========================================================

    def _comprobar_gpu(self):

        if not torch.cuda.is_available():

            raise RuntimeError(
                "CUDA no está disponible. AFU V4 necesita la GPU."
            )

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

        print(
            "VRAM:",
            round(
                torch.cuda.get_device_properties(0).total_memory
                / 1024**3,
                2
            ),
            "GB"
        )

    # ========================================================
    # CARGAR MODELO
    # ========================================================

    def _cargar_modelo(self):

        print("\nCargando tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.BASE_MODEL
        )

        print("✅ Tokenizer cargado")

        print("\nConfigurando cuantización 4-bit...")

        bnb_config = BitsAndBytesConfig(

            load_in_4bit=True,

            bnb_4bit_quant_type="nf4",

            bnb_4bit_use_double_quant=True,

            bnb_4bit_compute_dtype=torch.float16
        )

        print("✅ Cuantización configurada")

        print("\nCargando Qwen2.5-1.5B...")

        base_model = AutoModelForCausalLM.from_pretrained(

            self.BASE_MODEL,

            quantization_config=bnb_config,

            device_map={"": 0},

            dtype=torch.float16
        )

        print("✅ Modelo base cargado")

        print("\nCargando adaptador AFU V4...")

        self.model = PeftModel.from_pretrained(

            base_model,

            self.ADAPTER_PATH
        )

        self.model.eval()

        print("✅ Adaptador AFU V4 cargado")

        print("\n" + "=" * 70)
        print("✅ AFU V4 LISTO PARA RESPONDER")
        print("=" * 70)

    # ========================================================
    # GENERAR RESPUESTA
    # ========================================================

    def preguntar(
        self,
        pregunta,
        ficha=None
    ):

        contexto = ""

        if ficha:

            contexto = self._crear_contexto(
                ficha
            )

        mensaje_usuario = pregunta

        if contexto:

            mensaje_usuario = f"""
ANIMAL IDENTIFICADO POR EL CLASIFICADOR:

{contexto}

PREGUNTA DEL USUARIO:

{pregunta}

Responde la pregunta teniendo en cuenta el animal identificado. No inventes información que no conozcas.
""".strip()

        mensajes = [

            {
                "role": "system",
                "content": self.SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": mensaje_usuario
            }
        ]

        texto = self.tokenizer.apply_chat_template(

            mensajes,

            tokenize=False,

            add_generation_prompt=True
        )

        inputs = self.tokenizer(

            texto,

            return_tensors="pt"
        ).to(
            self.model.device
        )

        with torch.no_grad():

            outputs = self.model.generate(

                **inputs,

                max_new_tokens=140,

                do_sample=False,

                repetition_penalty=1.15,

                pad_token_id=self.tokenizer.eos_token_id
            )

        nuevos_tokens = outputs[
            0,
            inputs["input_ids"].shape[1]:
        ]

        respuesta = self.tokenizer.decode(

            nuevos_tokens,

            skip_special_tokens=True
        )

        return respuesta.strip()

    # ========================================================
    # CONVERTIR FICHA A CONTEXTO
    # ========================================================

    def _crear_contexto(self, ficha):

        if isinstance(ficha, dict):

            partes = []

            for clave, valor in ficha.items():

                partes.append(
                    f"{clave}: {valor}"
                )

            return "\n".join(partes)

        return str(ficha)


# ============================================================
# INSTANCIA ÚNICA
# ============================================================

