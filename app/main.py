from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
import time
from docx import Document

from app.converter import docx_to_pdf
from app.gemini_service import analyze_pdf

from fastapi.middleware.cors import CORSMiddleware

UPLOAD_FOLDER = "uploads"
PDF_FOLDER = "pdfs"

# Constantes de validación
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB en bytes
ALLOWED_EXTENSIONS = ['.docx']

"""Creación de las carpetas para almacenamiento temporal de los archivos"""
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

app = FastAPI()
"""Autorización al front de enviar información a la API"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...), tipo_formato: str = "estandar"):
    start_time = time.time()
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    pdf_path = None

    try:
        # Validar extensión del archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Solo se permiten archivos Word (.docx). Archivo recibido: {file_extension}"
            )

        # Validar tamaño del archivo
        file.file.seek(0, 2)  # Ir al final del archivo
        file_size = file.file.tell()  # Obtener tamaño
        file.file.seek(0)  # Volver al inicio
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo supera el tamaño máximo permitido de 100 MB. Tamaño: {file_size / (1024*1024):.2f} MB"
            )

        """ Guardar el archivo Word """
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        """ Convertir a PDF """
        pdf_path = docx_to_pdf(file_path, PDF_FOLDER)

        """ Analizar el PDF con Gemini según el tipo de formato """
        analysis_data = analyze_pdf(pdf_path, tipo_formato)

        """ Calcular tiempo de procesamiento """
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        """ Agregar el nombre del archivo y tiempo a la respuesta """
        response = {
            "nombre_archivo": file.filename,
            "tiempo_procesamiento_backend": processing_time,
            **analysis_data
        }

        return response
    
    finally:
        """Eliminar archivos después de procesarlos"""
        if os.path.exists(file_path):
            os.remove(file_path)
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)


@app.get("/")
def root():
    return {"message": "API funcionando"}