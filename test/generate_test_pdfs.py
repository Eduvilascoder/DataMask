"""
Script para generar PDFs de ejemplo con datos sensibles ficticios argentinos.

Genera 3 archivos PDF en la carpeta test/ para verificar el correcto
funcionamiento de la ofuscación de datos sensibles.

Uso:
    python test/generate_test_pdfs.py

IMPORTANTE: Todos los datos son FICTICIOS y no corresponden a personas reales.
"""

import os

from fpdf import FPDF
from fpdf.enums import XPos, YPos


# Directorio de salida (misma carpeta donde está el script)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_output_dir() -> None:
    """Crea el directorio de salida si no existe."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _cell(pdf: FPDF, w: int, h: int, text: str, **kwargs) -> None:
    """Helper para escribir una celda con nueva linea."""
    kwargs.setdefault("align", "")
    pdf.cell(w, h, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, **kwargs)


def generate_formulario_registro() -> None:
    """
    Genera PDF 1: Formulario de registro.

    Datos ficticios incluidos:
    - Nombre: María Fernanda González López
    - DNI: 32.456.789
    - Email: maria.gonzalez@correo.com.ar
    - Teléfono: +54 11 4567 8901
    - Dirección: Av. Corrientes 1234, Piso 5, CABA, Buenos Aires
    - CUIT: 27-32456789-4
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Titulo
    pdf.set_font("Helvetica", "B", 16)
    _cell(pdf, 0, 10, "FORMULARIO DE REGISTRO", align="C")
    pdf.ln(10)

    # Subtitulo
    pdf.set_font("Helvetica", "I", 10)
    _cell(pdf, 0, 6, "Documento interno - Uso administrativo", align="C")
    pdf.ln(10)

    # Contenido del formulario
    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "DATOS PERSONALES")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    _cell(pdf, 0, 7, "Nombre completo: Maria Fernanda Gonzalez Lopez")
    _cell(pdf, 0, 7, "DNI: 32.456.789")
    _cell(pdf, 0, 7, "Correo electronico: maria.gonzalez@correo.com.ar")
    _cell(pdf, 0, 7, "Telefono: +54 11 4567 8901")
    _cell(
        pdf, 0, 7,
        "Direccion: Av. Corrientes 1234, Piso 5, CABA, Buenos Aires",
    )
    _cell(pdf, 0, 7, "CUIT: 27-32456789-4")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "INFORMACION ADICIONAL")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 7,
        "La solicitante Maria Fernanda Gonzalez Lopez, identificada con "
        "DNI 32.456.789 y CUIT 27-32456789-4, solicita el alta en el "
        "sistema de gestion. Se puede contactar al telefono +54 11 4567 8901 "
        "o al correo maria.gonzalez@correo.com.ar para cualquier consulta "
        "relacionada con este tramite.",
    )
    pdf.ln(8)

    pdf.multi_cell(
        0, 7,
        "Domicilio declarado: Av. Corrientes 1234, Piso 5, CABA, Buenos Aires. "
        "Se solicita verificacion del domicilio antes de proceder con la "
        "habilitacion de la cuenta.",
    )
    pdf.ln(10)

    # Pie de pagina
    pdf.set_font("Helvetica", "I", 9)
    _cell(
        pdf, 0, 6,
        "Este documento contiene datos personales protegidos por la Ley 25.326.",
        align="C",
    )

    output_path = os.path.join(OUTPUT_DIR, "formulario_registro.pdf")
    pdf.output(output_path)
    print(f"  Generado: {output_path}")


def generate_contrato_servicio() -> None:
    """
    Genera PDF 2: Contrato de servicio.

    Datos ficticios incluidos:
    - Nombre: Carlos Alberto Rodriguez
    - CUIT: 20-28765432-1
    - Direccion: Calle San Martin 567, Rosario, Santa Fe
    - CBU: 0170099220000012345678
    - Telefono: +54 341 4567 890
    - Email: carlos.rodriguez@empresa.com.ar
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Titulo
    pdf.set_font("Helvetica", "B", 16)
    _cell(pdf, 0, 10, "CONTRATO DE PRESTACION DE SERVICIOS", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    _cell(pdf, 0, 6, "Contrato N: 2024-00567", align="C")
    pdf.ln(10)

    # Cuerpo del contrato
    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "PARTES INTERVINIENTES")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 7,
        "Entre la empresa SERVICIOS TECNOLOGICOS S.A. y el Sr. Carlos Alberto "
        "Rodriguez, identificado con CUIT 20-28765432-1, con domicilio en "
        "Calle San Martin 567, Rosario, Santa Fe, se celebra el presente "
        "contrato de prestacion de servicios profesionales.",
    )
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "DATOS DEL PRESTADOR")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    _cell(pdf, 0, 7, "Nombre: Carlos Alberto Rodriguez")
    _cell(pdf, 0, 7, "CUIT: 20-28765432-1")
    _cell(pdf, 0, 7, "Domicilio: Calle San Martin 567, Rosario, Santa Fe")
    _cell(pdf, 0, 7, "CBU: 0170099220000012345678")
    _cell(pdf, 0, 7, "Email: carlos.rodriguez@empresa.com.ar")
    _cell(pdf, 0, 7, "Telefono de contacto: +54 341 4567 890")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "CLAUSULAS")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 7,
        "PRIMERA: El prestador Carlos Alberto Rodriguez se compromete a "
        "brindar servicios de consultoria informatica por un periodo de "
        "12 meses a partir de la firma del presente contrato.",
    )
    pdf.ln(5)

    pdf.multi_cell(
        0, 7,
        "SEGUNDA: Los honorarios seran depositados en la cuenta bancaria "
        "CBU 0170099220000012345678 a nombre del prestador, dentro de los "
        "primeros 5 dias habiles de cada mes. Cualquier consulta sobre "
        "pagos dirigirse a carlos.rodriguez@empresa.com.ar.",
    )
    pdf.ln(5)

    pdf.multi_cell(
        0, 7,
        "TERCERA: Para cualquier notificacion, se utilizara el domicilio "
        "declarado en Calle San Martin 567, Rosario, Santa Fe, o el "
        "telefono +54 341 4567 890.",
    )
    pdf.ln(10)

    # Pie
    pdf.set_font("Helvetica", "I", 9)
    _cell(
        pdf, 0, 6,
        "Documento confidencial - Contiene datos personales y financieros.",
        align="C",
    )

    output_path = os.path.join(OUTPUT_DIR, "contrato_servicio.pdf")
    pdf.output(output_path)
    print(f"  Generado: {output_path}")


def generate_ficha_empleado() -> None:
    """
    Genera PDF 3: Ficha de empleado.

    Datos ficticios incluidos:
    - Nombre: Ana Lucia Martinez Perez
    - DNI: 35678901
    - Email: ana.martinez@trabajo.com
    - Celular: +54 9 11 6789 0123
    - Pasaporte: AAB654321
    - Tarjeta de credito: 4532-1234-5678-9012
    - Direccion: Belgrano 890, Mendoza, Mendoza
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Titulo
    pdf.set_font("Helvetica", "B", 16)
    _cell(pdf, 0, 10, "FICHA DE EMPLEADO", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    _cell(pdf, 0, 6, "Legajo N: EMP-2024-0891", align="C")
    pdf.ln(10)

    # Datos personales
    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "DATOS PERSONALES")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    _cell(pdf, 0, 7, "Nombre completo: Ana Lucia Martinez Perez")
    _cell(pdf, 0, 7, "DNI: 35678901")
    _cell(pdf, 0, 7, "Correo electronico: ana.martinez@trabajo.com")
    _cell(pdf, 0, 7, "Celular: +54 9 11 6789 0123")
    _cell(pdf, 0, 7, "Pasaporte: AAB654321")
    _cell(pdf, 0, 7, "Direccion: Belgrano 890, Mendoza, Mendoza")
    pdf.ln(8)

    # Datos financieros
    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "DATOS FINANCIEROS")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    _cell(pdf, 0, 7, "Tarjeta corporativa: 4532-1234-5678-9012")
    pdf.ln(8)

    # Informacion laboral
    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "INFORMACION LABORAL")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    _cell(pdf, 0, 7, "Cargo: Analista de Sistemas Senior")
    _cell(pdf, 0, 7, "Area: Tecnologia de la Informacion")
    _cell(pdf, 0, 7, "Fecha de ingreso: 15/03/2022")
    _cell(pdf, 0, 7, "Modalidad: Tiempo completo")
    pdf.ln(8)

    # Observaciones
    pdf.set_font("Helvetica", "B", 12)
    _cell(pdf, 0, 8, "OBSERVACIONES")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 7,
        "La empleada Ana Lucia Martinez Perez, DNI 35678901, fue incorporada "
        "al equipo de desarrollo en marzo de 2022. Su contacto principal es "
        "el celular +54 9 11 6789 0123 y el correo ana.martinez@trabajo.com. "
        "Cuenta con pasaporte vigente AAB654321 para viajes corporativos.",
    )
    pdf.ln(5)

    pdf.multi_cell(
        0, 7,
        "Se le asigno la tarjeta corporativa 4532-1234-5678-9012 para "
        "gastos de representacion. Su domicilio registrado es "
        "Belgrano 890, Mendoza, Mendoza. Cualquier consulta administrativa "
        "dirigirse a RRHH.",
    )
    pdf.ln(10)

    # Pie
    pdf.set_font("Helvetica", "I", 9)
    _cell(
        pdf, 0, 6,
        "Informacion confidencial - Solo para uso interno de Recursos Humanos.",
        align="C",
    )

    output_path = os.path.join(OUTPUT_DIR, "ficha_empleado.pdf")
    pdf.output(output_path)
    print(f"  Generado: {output_path}")


def main() -> None:
    """Genera los 3 PDFs de ejemplo en la carpeta test/."""
    print("Generando PDFs de ejemplo con datos sensibles ficticios...")
    print(f"Directorio de salida: {OUTPUT_DIR}")
    print()

    create_output_dir()

    print("1. Formulario de registro:")
    generate_formulario_registro()

    print("2. Contrato de servicio:")
    generate_contrato_servicio()

    print("3. Ficha de empleado:")
    generate_ficha_empleado()

    print()
    print("Generacion completada exitosamente.")
    print("Los 3 PDFs de ejemplo se encuentran en la carpeta test/")


if __name__ == "__main__":
    main()
