import os
import pandas as pd
import json
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from collections import deque
from dotenv import load_dotenv

# ====================
# CONFIGURACIÓN GEMINI
# ====================
load_dotenv()  # Carga las variables de entorno desde el archivo .env
api_key = os.getenv("GEMINI_API_KEY")  # Lee la clave de la variable de entorno
if not api_key:
    raise ValueError("No se encontró la clave API de GEMINI en el archivo .env. Por favor, asegúrate de agregarla.")

genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-pro-exp-02-05",
    generation_config=generation_config
)

# ============================================
# RATE-LIMITER: para no exceder 10 llamadas/min
# ============================================
MAX_CALLS_PER_MINUTE = 10
call_times = deque()

def gemini_rate_limited_call(user_message):
    """
    Envía un mensaje a Gemini, asegurándose de no exceder 10 RPM.
    Bloquea la ejecución si se llega al límite.
    """
    while len(call_times) >= MAX_CALLS_PER_MINUTE and (time.time() - call_times[0] < 60):
        sleep_time = 60 - (time.time() - call_times[0])
        print(f"[RateLimiter] Se alcanzó el límite de llamadas por minuto. Durmiendo {sleep_time:.1f} seg...")
        time.sleep(sleep_time)

    while call_times and (time.time() - call_times[0] >= 60):
        call_times.popleft()

    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(user_message)

    call_times.append(time.time())

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"[ERROR] No se pudo decodificar el JSON: {e}")
        return []

# ==========================================
# FUNCIÓN PARA DIVIDIR EN BLOQUES POR TOKENS
# ==========================================
def divide_into_token_safe_batches(target_column, model, max_tokens, col_name):
    """
    Divide la lista 'target_column' en bloques de máximo 'max_tokens' tokens,
    procesando de 20 filas en 20 filas.
    """
    batches = []
    current_batch = []
    chunk_index = 1
    current_token_count = 0

    for i in range(0, len(target_column), 20):
        group_dicts = [{col_name: str(x)} for x in target_column[i : i + 20]]
        group_token_count = model.count_tokens(json.dumps(group_dicts, ensure_ascii=False, indent=4)).total_tokens

        if current_token_count + group_token_count > max_tokens:
            if current_batch:
                batches.append(current_batch)
                print(f"[INFO] Agrupado bloque {chunk_index}...")
                chunk_index += 1
            current_batch = group_dicts
            current_token_count = group_token_count
        else:
            current_batch.extend(group_dicts)
            current_token_count += group_token_count

    if current_batch:
        batches.append(current_batch)
        print(f"[INFO] Agrupado bloque {chunk_index}...")

    return batches

def process_block(batch, batch_idx, total_batches):
    """
    Prepara el prompt y realiza la llamada a Gemini.
    """
    batch_json = json.dumps(batch, ensure_ascii=False)

    user_message = (
        "A continuación se te proporciona una lista de comentarios. Para cada comentario, clasifícalo en dos campos:\n\n"
        "1. 'Tópico Comentario': Elige una de las siguientes opciones exactamente como están escritas:\n"
        "   - Curso\n"
        "   - Docente\n"
        "   - Plataforma\n"
        "   - Modalidad\n"
        "   - Encuesta ESA\n"
        "   - Horario\n"
        "   - Trabajos\n"
        "   - Atención al estudiante\n"
        "   - Si no se aplica ninguna de las anteriores, o si el comentario no es claro o no se puede determinar, deja este campo vacío (\"\")\n\n"
        "2. 'Clasificación Comentario': Elige una de las siguientes opciones exactamente como están escritas:\n"
        "   - Positivo\n"
        "   - Negativo\n"
        "   - Neutro\n"
        "   - Si no se aplica ninguna de las anteriores, o si el comentario no es claro o no se puede determinar, deja este campo vacío (\"\")\n\n"
        "Devuelve únicamente un arreglo JSON válido de objetos, donde cada objeto tenga la siguiente estructura:\n\n"
        "{\n"
        "  \"Comentario\": \"texto_original_del_comentario\",\n"
        "  \"Tópico Comentario\": \"tópico_seleccionado\",\n"
        "  \"Clasificación Comentario\": \"clasificación_seleccionada\"\n"
        "}\n\n"
        "No incluyas texto adicional, explicaciones ni claves extra. Asegúrate de que el JSON sea válido, sin comas al final ni claves adicionales.\n\n"
        "Aquí está la lista de comentarios: " + batch_json
    )

    print(f"[INFO] Ejecutando bloque {batch_idx}/{total_batches}...")
    result = gemini_rate_limited_call(user_message)
    return result if isinstance(result, list) else []

def classify_using_gemini(target_column):
    """
    Procesa en lotes los comentarios y clasifica con Gemini.
    """
    matches = []
    batches = divide_into_token_safe_batches(target_column, model, max_tokens=4000, col_name="Comentario")
    total_batches = len(batches)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_index = {executor.submit(process_block, batch, idx, total_batches): idx for idx, batch in enumerate(batches, start=1)}
        for future in as_completed(future_to_index):
            batch_idx = future_to_index[future]
            try:
                matches.extend(future.result())
            except Exception as e:
                print(f"[ERROR] Bloque {batch_idx} falló: {e}")

    return matches

if __name__ == "__main__":
    try:
        input_file = os.getenv("INPUT_FILE")
        if input_file:
            input_file = input_file.replace("\\", "/")  # Convierte barras invertidas a barras normales

        sheet_name = os.getenv("SHEET_NAME")
        column_name = os.getenv("COLUMN_NAME")
        
        if not input_file or not sheet_name or not column_name:
            raise ValueError("Faltan variables de entorno necesarias: INPUT_FILE, SHEET_NAME o COLUMN_NAME.")
        
        comments = pd.read_excel(input_file, sheet_name=sheet_name)[column_name].dropna().drop_duplicates().tolist()
        results = classify_using_gemini(comments)
        output_file = "ColumnClassifier.xlsx"
        pd.DataFrame(results).to_excel(output_file, index=False)
        print(f"[OK] Se generó el archivo de resultados: {output_file}")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado: {e}")

input("Presiona Enter para cerrar...")
