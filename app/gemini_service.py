import google.genai as genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_pdf(pdf_path: str, tipo_formato: str = "new_inntech", nombre_archivo: str = ""):
    """
    Analiza un documento PDF usando Gemini, extrayendo información de calidad
    
    Args:
        pdf_path: Ruta al archivo PDF
        tipo_formato: Tipo de formato del documento
        nombre_archivo: Nombre del archivo adjuntado
    """
    
    # Configuración de logos según el tipo de formato
    logos_config = {
        "corona": {
            "logos_requeridos": ["Logo New Inntech", "Logo Corona"]
        },
        "linea_directa": {
            "logos_requeridos": ["Logo New Inntech", "Logo Línea Directa"]
        },
        "new_inntech": {
            "logos_requeridos": ["Logo New Inntech"]
        },
        "novaventa": {
            "logos_requeridos": ["Logo New Inntech", "Logo Netw", "Logo Novaventa", "Logo Nutresa"]
        },
        "nutresa_netw": {
            "logos_requeridos": ["Logo New Inntech", "Logo Netw", "Logo Nutresa"]
        },
        "nutresa_proyectos": {
            "logos_requeridos": ["Logo New Inntech", "Logo Nutresa"]
        },
        "web_back": {
            "logos_requeridos": ["Logo New Inntech"]
        },
        "web_front": {
            "logos_requeridos": ["Logo New Inntech"]
        }
    }
    
    config = logos_config.get(tipo_formato, logos_config["new_inntech"])
    logos_requeridos_str = ", ".join(config["logos_requeridos"])
    
    prompt = f"""
    Analiza el siguiente documento PDF de acuerdo a los estándares de calidad de New Inntech.

    TIPO DE FORMATO: {tipo_formato.upper()}
    LOGOS REQUERIDOS EN EL ENCABEZADO: {logos_requeridos_str}

    ESTÁNDARES DE CALIDAD A VALIDAR:
    1. Formato: Letra Calibri 12, color negro en contenido (excepto encabezado), en los bloques de código no importa el color de la letra ni tipo o tamaño
    2. Tabla de contenido: Mínimo una hoja propia, sin negrita(Solo en el titulo "Contenido"), sin puntos, páginas coherentes
    3. Tabla de datos generales: Debe estar completa (excepto campo "código" que es opcional)
    4. Tabla de condiciones de uso: Si no está vacía, debe tener márgenes(Tener excesiva atención a esto)
    5. Encabezado: Debe contener los logos requeridos: {logos_requeridos_str}
    6. Contenido: Información concisa, técnica y funcional
    7. Espacios: No más de media página de espacios en blanco (excepto después de portada, tabla de contenido y ultima página)
    8. Código: No importa ningún tipo de falla ortografica

    Debes responder ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
    {{
        "nombre_archivo": "{nombre_archivo}",
        "proyecto": "nombre del proyecto",
        "lider": "nombre del líder",
        "compania": "nombre de la compañía",
        "tipo_ejecucion": "tipo de ejecución",
        "porcentaje_aprobacion": 85,
        "fragmentos_mejora": [
            {{
                "pagina": 1,
                "fragmento": "texto exacto del documento donde se necesita mejora",
                "recomendacion": "descripción específica de cómo mejorar este fragmento"
            }}
        ],
        "indicadores_faltantes": [
            {{
                "aspecto": "nombre del aspecto faltante",
                "descripcion": "descripción de qué información hace falta",
                "impacto": "impacto en la calidad del documento"
            }}
        ]
    }}

    INSTRUCCIONES CRÍTICAS:
    - El porcentaje_aprobacion debe ser un número entre 0 y 100
    - Para fragmentos_mejora: extrae TEXTO EXACTO del documento, no parafrasees
    - Incluye solo fragmentos donde REALMENTE se necesite mejora
    - Para indicadores_faltantes: identifica qué información del estándar de calidad NO está en el documento y NO LO PONGAS si de verdad mo está incumplido
    - Si no encuentras algún campo de información básica, usa "No especificado" Que falte el lider o la compañía no es un error crítico
    - Responde SOLO con el JSON, sin texto adicional antes o después
    """

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf"
            )
        ]
    )

    # Extraer JSON de la respuesta
    response_text = response.text.strip()
    
    # Intentar extraer JSON si viene con markdown
    if "```json" in response_text:
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
    elif "```" in response_text:
        json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Si falla el parsing, devolver estructura básica
        return {
            "nombre_archivo": "No especificado",
            "proyecto": "No especificado",
            "lider": "No especificado",
            "compania": "No especificado",
            "tipo_ejecucion": "No especificado",
            "porcentaje_aprobacion": 0,
            "fragmentos_mejora": [],
            "indicadores_faltantes": []
        }
