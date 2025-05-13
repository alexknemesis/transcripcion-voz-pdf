# E:\PROJECTS\voice_test\assemblyai_service.py

import os
import asyncio
import httpx
from fastapi import HTTPException

# Constante para la URL base de AssemblyAI
ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"

async def upload_audio_to_assemblyai(client: httpx.AsyncClient, file_content: bytes, api_key: str) -> str:
    upload_endpoint = f"{ASSEMBLYAI_BASE_URL}/upload"
    headers = {"authorization": api_key}
    print("Subiendo archivo a AssemblyAI...")
    try:
        response = await client.post(upload_endpoint, headers=headers, content=file_content)
        response.raise_for_status()
        result = response.json()
        print(f"Archivo subido exitosamente. URL: {result['upload_url']}")
        return result["upload_url"]
    except httpx.HTTPStatusError as e:
        error_detail = "No se pudo obtener detalle del error"; 
        try: error_detail = e.response.json().get("error", e.response.text)
        except: pass
        print(f"Error HTTP al subir archivo a AssemblyAI: {e.response.status_code} - {error_detail}")
        raise HTTPException(status_code=502, detail=f"Error de AssemblyAI al subir archivo ({e.response.status_code}): {error_detail}")
    except Exception as e:
        print(f"Error inesperado al subir archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno al subir archivo: {str(e)}")

async def request_transcription(client: httpx.AsyncClient, audio_url: str, api_key: str) -> str:
    transcript_endpoint = f"{ASSEMBLYAI_BASE_URL}/transcript"
    headers = {"authorization": api_key, "content-type": "application/json"}
    data = {
        "audio_url": audio_url, "speech_model": "universal", "language_code": "es",
        "punctuate": True, "format_text": True, "speaker_labels": False 
    }
    print(f"Solicitando transcripción para la URL: {audio_url} con parámetros: {data}")
    try:
        response = await client.post(transcript_endpoint, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"Solicitud de transcripción enviada. ID: {result['id']}")
        return result["id"]
    except httpx.HTTPStatusError as e:
        error_detail = "No se pudo obtener detalle del error"; 
        try: error_detail = e.response.json().get("error", e.response.text)
        except: pass
        print(f"Error HTTP al solicitar transcripción: {e.response.status_code} - {error_detail}")
        raise HTTPException(status_code=502, detail=f"Error de AssemblyAI al solicitar transcripción ({e.response.status_code}): {error_detail}")
    except Exception as e:
        print(f"Error inesperado al solicitar transcripción: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno al solicitar transcripción: {str(e)}")

async def poll_for_transcription_result(client: httpx.AsyncClient, transcript_id: str, api_key: str) -> dict:
    polling_endpoint = f"{ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}"
    headers = {"authorization": api_key}
    while True:
        print(f"Consultando estado de la transcripción ID: {transcript_id}...")
        try:
            response = await client.get(polling_endpoint, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result['status'] == 'completed':
                print("Transcripción completada.")
                return result
            elif result['status'] == 'error':
                error_msg = result.get('error', 'Error desconocido en la transcripción de AssemblyAI.')
                print(f"Error en la transcripción de AssemblyAI: {error_msg}")
                raise HTTPException(status_code=400, detail=f"Error de AssemblyAI en la transcripción: {error_msg}")
            elif result['status'] in ['queued', 'processing']:
                print(f"Estado de la transcripción: {result['status']}. Esperando 5 segundos...")
                await asyncio.sleep(5)
            else:
                print(f"Estado desconocido de AssemblyAI: {result['status']}")
                raise HTTPException(status_code=500, detail=f"Estado de transcripción desconocido de AssemblyAI: {result['status']}")
        except httpx.HTTPStatusError as e:
            error_detail = "No se pudo obtener detalle del error"; 
            try: error_detail = e.response.json().get("error", e.response.text)
            except: pass
            print(f"Error HTTP al consultar transcripción: {e.response.status_code} - {error_detail}")
            raise HTTPException(status_code=502, detail=f"Error de AssemblyAI al obtener resultado de transcripción ({e.response.status_code}): {error_detail}")
        except Exception as e:
            print(f"Error inesperado al consultar transcripción: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error interno al obtener resultado: {str(e)}")