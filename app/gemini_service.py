import google.genai as genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_pdf(pdf_path: str, tipo_formato: str = "estandar"):
    """
    Analiza un documento PDF usando Gemini, extrayendo información estructurada y validando formato
    
    Args:
        pdf_path: Ruta al archivo PDF
        tipo_formato: Tipo de formato del documento (estandar, tecnico, funcional, cliente)
    """
    
    # Configuración de logos según el tipo de formato
    logos_config = {
        "estandar": {
            "logos_requeridos": ["Logo de la compañía"],
            "descripcion": "Formato estándar con logo de la compañía"
        },
        "tecnico": {
            "logos_requeridos": ["Logo de la compañía", "Logo técnico"],
            "descripcion": "Formato técnico con logos de compañía y técnico"
        },
        "funcional": {
            "logos_requeridos": ["Logo de la compañía", "Logo funcional"],
            "descripcion": "Formato funcional con logos de compañía y funcional"
        },
        "cliente": {
            "logos_requeridos": ["Logo de la compañía", "Logo del cliente"],
            "descripcion": "Formato para cliente con logos de compañía y cliente"
        }
    }
    
    config = logos_config.get(tipo_formato, logos_config["estandar"])
    logos_requeridos_str = ", ".join(config["logos_requeridos"])
    
    prompt = f"""
    Analiza el siguiente documento PDF y valida tanto el formato como el contenido según las siguientes reglas.

    TIPO DE FORMATO: {tipo_formato.upper()}
    LOGOS REQUERIDOS EN EL ENCABEZADO: {logos_requeridos_str}

    VALIDACIONES DE FORMATO:
    1. La letra debe ser Calibri 12 y color negro en todo el contenido (excepto encabezado)
    2. La tabla de contenido debe tener mínimo una hoja propia, sin negrita, sin puntos, y las páginas deben ser coherentes
    3. La tabla de datos generales de desarrollo debe estar llena (excepto el campo "código" que es opcional)
    4. Si la tabla de condiciones para su uso no está vacía, debe tener márgenes
    5. El encabezado debe contener los logos requeridos: {logos_requeridos_str}
    
    VALIDACIONES DE CONTENIDO:
    1. Los cambios deben estar documentados separados en front y back
    2. La información debe ser concisa, técnica y funcional
    3. No debe haber espacios en blanco de más de media página (excepto después de portada o tabla de contenido)
    4. El código no debe tener modificaciones en espacios, acentuación u ortografía

    Debes responder ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
    {{
        "proyecto": "nombre del proyecto",
        "lider": "nombre del líder del proyecto",
        "compania": "nombre de la compañía",
        "tipo_ejecucion": "tipo de ejecución del proyecto",
        "tipo_formato_detectado": "{tipo_formato}",
        "resumen": "resumen claro y conciso del contenido del documento",
        "puntos_principales": ["punto 1", "punto 2", "punto 3"],
        "validaciones_formato": {{
            "letra_calibri_12": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }},
            "tabla_contenido": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }},
            "tabla_datos_generales": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }},
            "tabla_condiciones_uso": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }},
            "logos_encabezado": {{
                "cumple": true/false,
                "logos_encontrados": ["lista de logos encontrados en el encabezado"],
                "logos_requeridos": {json.dumps(config["logos_requeridos"])},
                "observaciones": "descripción de qué logos faltan o están incorrectos"
            }}
        }},
        "validaciones_contenido": {{
            "cambios_documentados": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }},
            "informacion_concisa": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }},
            "espacios_excesivos": {{
                "cumple": true/false,
                "observaciones": "páginas con espacios excesivos si no cumple"
            }},
            "codigo_sin_modificar": {{
                "cumple": true/false,
                "observaciones": "descripción del problema si no cumple"
            }}
        }},
        "imagenes": [
            {{
                "pagina": 1,
                "descripcion": "descripción de la imagen"
            }}
        ],
        "informacion_detallada": [
            {{
                "pagina": 1,
                "contenido": "información importante encontrada"
            }}
        ],
        "cumplimiento_general": {{
            "porcentaje": 85,
            "estado": "Aprobado/Rechazado/Requiere correcciones"
        }}
    }}

    INSTRUCCIONES:
    - Si no encuentras algún campo de información básica, usa "No especificado"
    - Para la validación de logos, revisa el ENCABEZADO del documento y lista todos los logos que encuentres
    - Compara los logos encontrados con los requeridos: {logos_requeridos_str}
    - Para cada validación, indica si cumple (true/false) y proporciona observaciones detalladas
    - El porcentaje de cumplimiento es el promedio de todas las validaciones que cumplen
    - El estado es "Aprobado" si cumple >= 90%, "Requiere correcciones" si >= 70%, "Rechazado" si < 70%
    - Responde SOLO con el JSON, sin texto adicional antes o después
    """

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-1.5-flash",
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
            "proyecto": "No especificado",
            "lider": "No especificado",
            "compania": "No especificado",
            "tipo_ejecucion": "No especificado",
            "tipo_formato_detectado": tipo_formato,
            "resumen": "Error al procesar el documento",
            "puntos_principales": [],
            "validaciones_formato": {
                "letra_calibri_12": {"cumple": False, "observaciones": "No se pudo validar"},
                "tabla_contenido": {"cumple": False, "observaciones": "No se pudo validar"},
                "tabla_datos_generales": {"cumple": False, "observaciones": "No se pudo validar"},
                "tabla_condiciones_uso": {"cumple": False, "observaciones": "No se pudo validar"},
                "logos_encabezado": {
                    "cumple": False, 
                    "logos_encontrados": [],
                    "logos_requeridos": config["logos_requeridos"],
                    "observaciones": "No se pudo validar"
                }
            },
            "validaciones_contenido": {
                "cambios_documentados": {"cumple": False, "observaciones": "No se pudo validar"},
                "informacion_concisa": {"cumple": False, "observaciones": "No se pudo validar"},
                "espacios_excesivos": {"cumple": False, "observaciones": "No se pudo validar"},
                "codigo_sin_modificar": {"cumple": False, "observaciones": "No se pudo validar"}
            },
            "imagenes": [],
            "informacion_detallada": [],
            "cumplimiento_general": {
                "porcentaje": 0,
                "estado": "Error en validación"
            }
        }
