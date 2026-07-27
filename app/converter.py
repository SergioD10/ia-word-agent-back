import os
import subprocess

"""Función encargada de convertir los archivos docx a pdf"""
def docx_to_pdf(input_path: str, output_dir: str = "pdfs") -> str:
    """
    Convierte un archivo DOCX a PDF
    
    Args:
        input_path: Ruta del archivo DOCX de entrada
        output_dir: Directorio de salida para el PDF
    
    Returns:
        str: Ruta del archivo PDF generado
    """
    os.makedirs(output_dir, exist_ok=True)

    filename: str = os.path.splitext(os.path.basename(input_path))[0]
    pdf_path: str = os.path.join(output_dir, filename + ".pdf")

    if os.name == "nt":
        from docx2pdf import convert
        convert(input_path, pdf_path)
    else:
        result = subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_dir,
                input_path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0 or not os.path.exists(pdf_path):
            raise RuntimeError(
                "No fue posible convertir el archivo DOCX a PDF con LibreOffice. "
                f"Salida: {result.stdout} | Error: {result.stderr}"
            )

    return pdf_path