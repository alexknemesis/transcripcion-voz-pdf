# Transcripción de Voz a PDF para Historias Clínicas Odontológicas

Este proyecto permite convertir grabaciones de voz de dictados odontológicos en documentos PDF estructurados. Utiliza tecnologías de IA para transcribir el audio, analizar el contenido y generar un informe profesional en formato PDF.

## Características Principales

- **Transcripción de Audio**: Convierte dictados de voz en texto utilizando AssemblyAI.
- **Análisis de Contenido**: Procesa el texto transcrito con Gemini AI para extraer información clínica relevante.
- **Generación de PDF**: Crea documentos PDF estructurados con la información extraída.
- **Odontograma Digital**: Incluye representación visual de hallazgos dentales.
- **API REST**: Interfaz FastAPI para integración con otros sistemas.

## Ejemplo de Uso

1. **Entrada**: Archivo de audio con dictado odontológico (ejemplo: `examples/voice_sample.mp3`)  

https://github.com/user-attachments/assets/dce766d2-3a48-4f29-90a8-f77bbec218ff


2. **Procesamiento**: Transcripción y análisis mediante IA
3. **Salida**: Documento PDF estructurado (ejemplo: `examples/output_file.pdf`) [HistoriaDental_Carlos_López_id__De_paciente_cuatro_5678_20250513_0321_4fbef8.pdf](https://github.com/user-attachments/files/20185068/HistoriaDental_Carlos_Lopez_id__De_paciente_cuatro_5678_20250513_0321_4fbef8.pdf)


## Requisitos

- Python 3.10 o superior
- Claves API:
  - AssemblyAI para transcripción de voz
  - Google Gemini para análisis de texto

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/alexknemesis/transcripcion-voz-pdf.git
cd transcripcion-voz-pdf

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
# Crear archivo .env con las siguientes variables:
# ASSEMBLYAI_API_KEY=tu_clave_api_assemblyai
# GEMINI_API_KEY=tu_clave_api_gemini
```

## Uso

### Iniciar el servidor API

```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

### Documentación de la API

Accede a la documentación interactiva en `http://localhost:8000/docs`

### Ejemplo de solicitud

```bash
curl -X POST "http://localhost:8000/dictado-a-pdf/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@examples/voice_sample.mp3"
```

## Estructura del Proyecto

```
transcripcion-voz-pdf/
├── assemblyai_service.py  # Servicios de transcripción de audio
├── gemini_service.py      # Servicios de análisis de texto con IA
├── pdf_generator.py       # Generación de documentos PDF
├── main.py                # Aplicación FastAPI principal
├── DejaVuSans*.ttf        # Fuentes para la generación de PDF
└── examples/              # Ejemplos de archivos de entrada y salida
    ├── voice_sample.mp3   # Ejemplo de archivo de audio
    └── output_file.pdf    # Ejemplo de PDF generado
```

## Flujo de Trabajo

1. **Carga de Audio**: El usuario envía un archivo de audio con un dictado odontológico.
2. **Transcripción**: AssemblyAI convierte el audio en texto.
3. **Análisis**: Gemini AI procesa el texto para extraer información estructurada.
4. **Generación de PDF**: Se crea un documento PDF con la información extraída.
5. **Respuesta**: Se devuelve el PDF al usuario.

## Tecnologías Utilizadas

- **FastAPI**: Framework web para la API REST
- **AssemblyAI**: Servicio de transcripción de voz a texto
- **Google Gemini**: Modelo de IA para análisis de texto
- **FPDF**: Biblioteca para generación de documentos PDF
- **Python**: Lenguaje de programación principal

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios propuestos.
