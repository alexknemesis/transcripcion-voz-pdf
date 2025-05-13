# E:\PROJECTS\voice_test\main_refactorizado.py

import os
import asyncio
import json
import io
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
import httpx
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

# Importar los módulos refactorizados
from assemblyai_service import upload_audio_to_assemblyai, request_transcription, poll_for_transcription_result
from gemini_service import analyze_text_with_gemini
from pdf_generator import create_pdf_from_json

# Cargar variables de entorno del archivo .env
load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    print("ADVERTENCIA: ASSEMBLYAI_API_KEY no encontrada. La transcripción fallará.")
if not GEMINI_API_KEY:
    print("ADVERTENCIA: GEMINI_API_KEY no encontrada. El análisis de texto fallará.")

app = FastAPI(
    title="Mi API de Dictado Dental IA con Odontograma",
    description="API para transcribir audio dental, analizarlo con IA, generar un JSON estructurado y un PDF.",
    version="0.4.0" # Versión actualizada por refactorización
)

@app.post("/dictado-a-pdf/")
async def dictado_a_pdf_endpoint(audio_file: UploadFile = File(...)):
    if not ASSEMBLYAI_API_KEY or not GEMINI_API_KEY:
         raise HTTPException(status_code=500, detail="Una o más API Keys no están configuradas en el servidor.")
    if not audio_file:
        raise HTTPException(status_code=400, detail="No se proporcionó ningún archivo de audio.")

    print(f"Archivo recibido: {audio_file.filename}, tipo: {audio_file.content_type}")
    file_content = await audio_file.read()
    await audio_file.close()

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=20.0)) as client:
        try:
            print("--- Iniciando Transcripción con AssemblyAI ---")
            uploaded_audio_url = await upload_audio_to_assemblyai(client, file_content, ASSEMBLYAI_API_KEY)
            transcript_id = await request_transcription(client, uploaded_audio_url, ASSEMBLYAI_API_KEY)
            transcription_result = await poll_for_transcription_result(client, transcript_id, ASSEMBLYAI_API_KEY)
            transcribed_text = transcription_result.get('text')
            if not transcribed_text:
                raise HTTPException(status_code=500, detail="La transcripción no produjo texto.")
            
            print(f"--- Texto Transcrito (primeros 200 chars): {transcribed_text[:200]}... ---")

            print("--- Iniciando Análisis con Gemini para extraer JSON ---")
            extracted_json_data = await analyze_text_with_gemini(transcribed_text, transcript_id, GEMINI_API_KEY)
            
            if not isinstance(extracted_json_data, dict):
                print(f"Error: Gemini no devolvió un diccionario JSON válido. Recibido: {type(extracted_json_data)}")
                raise HTTPException(status_code=500, detail="La IA no generó una estructura de datos válida.")

            if "texto_transcrito_original" not in extracted_json_data or not extracted_json_data["texto_transcrito_original"]:
                extracted_json_data["texto_transcrito_original"] = transcribed_text

            print("--- JSON Estructurado por Gemini (parcial): ---")
            print(json.dumps(extracted_json_data, indent=2, ensure_ascii=False)[:500])

            print("--- Generando PDF ---")
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(None, create_pdf_from_json, extracted_json_data)
            print(f"PDF generado en memoria ({len(pdf_bytes)} bytes).")
            if not pdf_bytes:
                raise HTTPException(status_code=500, detail="La generación del PDF resultó en un archivo vacío.")

            paciente_id_raw = extracted_json_data.get("paciente_identificador_mencionado_opcional", "desconocido")
            paciente_id = str(paciente_id_raw).replace(" ", "_").replace("/", "_").replace("\\", "_") if paciente_id_raw else "desconocido"
            
            fecha_consulta_raw = extracted_json_data.get("fecha_hora_dictado_aproximada", datetime.utcnow().isoformat())
            try:
                if fecha_consulta_raw.endswith('Z'):
                    dt_obj = datetime.fromisoformat(fecha_consulta_raw.replace("Z", "+00:00"))
                else:
                    dt_obj = datetime.fromisoformat(fecha_consulta_raw)
                    if dt_obj.tzinfo is None: 
                        dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)
                fecha_consulta_clean = dt_obj.strftime("%Y%m%d_%H%M")
            except Exception as date_e:
                print(f"Error parseando fecha '{fecha_consulta_raw}': {date_e}")
                fecha_consulta_clean = "fecha_invalida"

            pdf_filename_base = f"HistoriaDental_{paciente_id}_{fecha_consulta_clean}_{transcript_id[:6]}"
            pdf_filename_safe = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in pdf_filename_base) + ".pdf"
            
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=\"{pdf_filename_safe}\""}
            )
        except HTTPException as e:
            raise e
        except RuntimeError as e: 
            print(f"Error de Runtime durante la generación del PDF o flujo: {str(e)}")
            import traceback; traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")
        except Exception as e:
            print(f"Error general en /dictado-a-pdf/: {str(e)}")
            import traceback; traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Ocurrió un error interno inesperado en el servidor: {str(e)}")

# Punto de entrada para ejecutar la aplicación directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)