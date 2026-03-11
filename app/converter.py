from docx2pdf import convert
import os

"""Función encargada de convertir los archivos docx a pdf"""
def docx_to_pdf(input_path: str, output_dir: str = "pdfs"):

    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.splitext(os.path.basename(input_path))[0]
    pdf_path = os.path.join(output_dir, filename + ".pdf")

    convert(input_path, pdf_path)

    return pdf_path