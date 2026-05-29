"""
Script para generar PDFs de ejemplo con datos sensibles ficticios argentinos.

Este archivo es un wrapper de conveniencia que invoca el script principal
ubicado en scripts/generate_test_pdfs.py.

Uso:
    python generate_test_pdfs.py

IMPORTANTE: Todos los datos son FICTICIOS y no corresponden a personas reales.
"""

import runpy
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ejecutar el script principal
runpy.run_path(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "scripts",
        "generate_test_pdfs.py",
    ),
    run_name="__main__",
)
