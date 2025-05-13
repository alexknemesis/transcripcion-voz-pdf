# E:\PROJECTS\voice_test\gemini_service.py

import os
import json
import asyncio
from datetime import datetime
from fastapi import HTTPException
import google.generativeai as genai

def build_gemini_prompt(transcribed_text: str, assemblyai_id: str, current_timestamp: str) -> str:
    json_structure_example = """
{
  "paciente_identificador_mencionado_opcional": "string",
  "fecha_hora_dictado_aproximada": "YYYY-MM-DDTHH:MM:SSZ",
  "texto_transcrito_original": "string",
  "queja_principal_detectada": "string",
  "historia_enfermedad_actual_detectada": "string",
  "antecedentes_medicos_relevantes_detectados": ["string"],
  "hallazgos_examen_extraoral_detectados": "string",
  "hallazgos_examen_intraoral_general_detectados": "string",
  "odontograma_completo": {
    "18": { "diagnostico_hallazgo": "string", "plan_tratamiento_sugerido": "string", "notas_adicionales": "string" }
  },
  "diagnosticos_sugeridos_ia": ["string"],
  "procedimientos_realizados_sesion_detectados": [
    {
      "pieza_o_region_tratada": "string",
      "descripcion_procedimiento": "string",
      "anestesia_mencionada": "string",
      "materiales_mencionados": "string",
      "complicaciones_mencionadas": "string"
    }
  ],
  "indicaciones_postoperatorias_detectadas": "string",
  "medicacion_recetada_detectada": "string",
  "plan_proxima_cita_detectado": "string",
  "observaciones_generales_dictadas": "string"
}
"""
    prompt = f"""
Eres un asistente experto en extraer información de dictados de consultas odontológicas y formatearla en JSON.
Analiza el siguiente texto de una consulta odontológica:

--- INICIO TEXTO TRANSCRITO ---
{transcribed_text}
--- FIN TEXTO TRANSCRITO ---

Extrae la información relevante y formatea la salida ÚNICAMENTE como un objeto JSON válido que siga estrictamente la siguiente estructura.
Si alguna información no está presente en el texto, utiliza un string vacío "" para campos de texto, o una lista vacía `[]` para campos que esperan una lista, o un objeto vacío `{{}}` para "odontograma_completo" si no se menciona ninguna pieza.
Asegúrate de que el JSON sea parseable.

Estructura JSON esperada (parcial, para referencia de "odontograma_completo"):
{json_structure_example}

Instrucciones específicas:
- "paciente_identificador_mencionado_opcional": Si el dentista menciona un nombre o ID del paciente. Si no, string vacío.
- "fecha_hora_dictado_aproximada": Utiliza este valor que te proporciono: "{current_timestamp}".
- "texto_transcrito_original": Debe contener el texto completo transcrito que te he proporcionado arriba.
- "odontograma_completo": Este es un OBJETO donde las CLAVES son los números de las piezas dentales mencionadas (ej: "16", "48"). SOLO incluye en este objeto las piezas que se mencionen explícitamente en el dictado con algún hallazgo, diagnóstico o plan. Para cada pieza mencionada, crea un objeto con los campos:
    - "diagnostico_hallazgo": Qué se encontró o diagnosticó en esa pieza. Si no se menciona, string vacío.
    - "plan_tratamiento_sugerido": Qué se planea hacer para esa pieza. Si no se menciona, string vacío.
    - "notas_adicionales": Cualquier otra nota específica para esa pieza. Si no se menciona, string vacío.
  Ejemplo para odontograma_completo si se menciona la pieza 16 y 48:
  "odontograma_completo": {{
    "16": {{ "diagnostico_hallazgo": "Caries mesial profunda", "plan_tratamiento_sugerido": "Endodoncia y corona", "notas_adicionales": "Evaluar pronóstico" }},
    "48": {{ "diagnostico_hallazgo": "Sano, retenido", "plan_tratamiento_sugerido": "Exodoncia profiláctica", "notas_adicionales": "Cercano a nervio dentario" }}
  }}
  Si no se menciona ninguna pieza específica con detalles, "odontograma_completo" debe ser un objeto vacío: {{}}.
- Todos los demás campos (queja_principal, historia_enfermedad, etc.) deben llenarse como se describió anteriormente (string vacío o lista vacía si no hay información).

No incluyas NINGÚN texto explicativo antes o después del JSON. La respuesta debe ser solo el JSON.
"""
    return prompt

async def analyze_text_with_gemini(transcribed_text: str, assemblyai_id: str, api_key: str) -> dict:
    if not api_key:
        raise HTTPException(status_code=500, detail="La API Key de Gemini no está configurada en el servidor.")
    try:
        target_model_name = 'models/gemini-1.5-flash-latest' 
        print(f"Intentando usar el modelo Gemini: {target_model_name}")
        
        current_timestamp_iso = datetime.utcnow().isoformat() + "Z"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=target_model_name,
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.2),
        )
        prompt_content = build_gemini_prompt(transcribed_text, assemblyai_id, current_timestamp_iso)
        print("Enviando solicitud a Gemini...")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt_content)
        print("Respuesta recibida de Gemini.")
        
        if not response.parts:
            error_message = "Respuesta inesperada de Gemini (sin partes)."
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                error_message = f"Solicitud a Gemini bloqueada. Razón: {response.prompt_feedback.block_reason.name}."
                if response.prompt_feedback.block_reason_message:
                     error_message += f" Mensaje: {response.prompt_feedback.block_reason_message}"
                print(f"Prompt Feedback de Gemini: {response.prompt_feedback}")
            print("Respuesta completa de Gemini (si falló):", response)
            raise HTTPException(status_code=400 if "bloqueada" in error_message else 502, detail=error_message)

        json_output_str = response.text
        
        if json_output_str.startswith("```json"):
            json_output_str = json_output_str.split("```json", 1)[-1]
        if json_output_str.startswith("```"):
            json_output_str = json_output_str[3:]
        if json_output_str.endswith("```"):
            json_output_str = json_output_str[:-3]
        json_output_str = json_output_str.strip()

        print(f"Texto JSON recibido de Gemini (antes de parsear, primeros 500 chars): {json_output_str[:500]}...")
        
        parsed_json = json.loads(json_output_str)
        print("JSON de Gemini parseado exitosamente.")
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"Error al parsear JSON de Gemini: {e}")
        print(f"String que falló al parsear:\n{json_output_str}")
        raise HTTPException(status_code=500, detail=f"Gemini devolvió un JSON malformado: {e}. Respuesta textual (parcial): {json_output_str[:1000]}")
    except genai.types.generation_types.BlockedPromptException as e_block:
        print(f"Solicitud a Gemini bloqueada por la SDK: {e_block}")
        raise HTTPException(status_code=400, detail=f"La solicitud a Gemini fue bloqueada por filtros de seguridad (SDK): {e_block}")
    except Exception as e:
        print(f"Error al interactuar con Gemini: {type(e).__name__} - {e}")
        error_detail = str(e)
        if hasattr(e, 'message'): error_detail = e.message
        elif hasattr(e, 'args') and e.args: error_detail = e.args[0]
        import traceback
        traceback.print_exc()
        if "permission_denied" in error_detail.lower() or "model not found" in error_detail.lower() or "404" in error_detail.lower():
            raise HTTPException(status_code=403, detail=f"Error de Gemini: Modelo '{target_model_name}' no encontrado o permiso denegado. Detalle: {error_detail}")
        raise HTTPException(status_code=502, detail=f"Error al procesar con Gemini: {error_detail}")