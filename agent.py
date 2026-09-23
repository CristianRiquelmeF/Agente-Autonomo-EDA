import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import skills  # Importamos nuestro módulo de herramientas

load_dotenv()  # Carga GEMINI_API_KEY (y otras variables) desde .env si existe

# Referencia a nivel de módulo: si el Client queda solo como variable local
# dentro de create_chat_session(), Python lo recolecta como basura al salir
# de la función y cierra el httpx.Client interno, aunque el objeto `chat`
# devuelto siga "vivo". Guardarlo aquí evita el error
# "Cannot send a request, as the client has been closed."
_client = None


def create_chat_session():
    """Inicializa el cliente de Gemini, configura las tools y devuelve la sesión de chat."""
    global _client

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se encontró GEMINI_API_KEY. Crea un archivo .env en la raíz del "
            "proyecto con la línea: GEMINI_API_KEY=tu_clave_aqui"
        )

    _client = genai.Client(api_key=api_key)

    # Inyectamos las funciones directamente desde el módulo skills
    config = types.GenerateContentConfig(
        tools=[
            skills.list_raw_files,
            skills.load_dataset,
            skills.get_info,
            skills.get_describe,
            skills.get_missing,
            skills.get_correlation,
            skills.plot_histogram,
            skills.plot_correlation_matrix,
            skills.generate_markdown_report,
            skills.run_full_eda,
        ],
        thinking_config=types.ThinkingConfig(thinking_level="high"),
    )

    return _client.chats.create(model="gemini-3.5-flash-lite", config=config)
