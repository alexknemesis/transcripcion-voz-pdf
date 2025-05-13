# E:\PROJECTS\voice_test\list_models.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno (asegúrate de que .env está en el mismo directorio o ajusta la ruta)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env') # Asume que .env está en el mismo dir que este script
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("Advertencia: Archivo .env no encontrado. Asegúrate de que GEMINI_API_KEY esté configurada como variable de entorno.")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY no está configurada. Por favor, configúrala en tu archivo .env o como variable de entorno.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

    print("Listando modelos disponibles para tu API Key que soportan 'generateContent':\n")
    
    # El SDK no tiene un método directo y simple para filtrar por 'generateContent' en el listado inicial,
    # pero podemos iterar y verificar. La propiedad 'supported_generation_methods' nos dice qué puede hacer cada modelo.
    
    found_models_for_generate_content = False
    for m in genai.list_models():
        # Para cada modelo, verificamos si 'generateContent' está en sus métodos soportados.
        # La documentación de la API de 'generativelanguage' indica que el método para
        # generar texto es 'generateContent'.
        if 'generateContent' in m.supported_generation_methods:
            print(f"  Nombre: {m.name}")
            print(f"    Display Name: {m.display_name}")
            print(f"    Description: {m.description[:100]}...") # Acortar descripción larga
            print(f"    Version: {m.version}")
            print(f"    Supported Generation Methods: {m.supported_generation_methods}")
            # Campos adicionales que pueden ser útiles:
            # print(f"    Input Token Limit: {m.input_token_limit}")
            # print(f"    Output Token Limit: {m.output_token_limit}")
            print("-" * 30)
            found_models_for_generate_content = True

    if not found_models_for_generate_content:
        print("No se encontraron modelos que soporten 'generateContent' con tu API Key.")
    
    print("\nConsideraciones:")
    print("- Los nombres de los modelos en la lista anterior son los que debes usar en `genai.GenerativeModel(model_name=...)`.")
    print("- Algunos modelos pueden requerir el prefijo 'models/' (ej: 'models/gemini-pro') y otros no (ej: 'gemini-pro'). La lista te dará el nombre exacto.")
    print("- Si un modelo que esperabas no aparece, es posible que tu API Key no tenga acceso a él, o que no soporte 'generateContent'.")