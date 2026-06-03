"""Tests para la redacción de fechas en PDFs.

Verifica que el método _search_date_fragments encuentra fechas
en PDFs incluso cuando los caracteres están en spans separados.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import fitz
import pytest

from app.models import DetectedEntity, SensitiveDataType, TypeConfig
from app.ner.engine import NEREngine
from app.pdf.processor import PDFProcessor
import json


def _make_engine(config: TypeConfig | None = None) -> NEREngine:
    """Helper: creates NEREngine with patterns from config file."""
    with open("config/types_config.json") as f:
        raw_config = json.load(f)
    engine = NEREngine(
        config=config or TypeConfig(),
        custom_types=raw_config,
    )
    engine._ollama_available = False  # Solo regex para tests determinísticos
    return engine


def _create_test_pdf_with_dates(path: str) -> None:
    """Crea un PDF de prueba con fechas en formato dd/mm/aa."""
    doc = fitz.open()
    page = doc.new_page()

    # Insertar texto con fechas
    text = (
        "Estado de Cuenta\n"
        "Facturación 18/11/25  Vencimiento 27/11/25\n"
        "Próximo Vencimiento 30/12/25\n"
        "Facturación anterior: 21/10/25\n"
        "DNI: 35.123.456\n"
        "CUIT: 20-35123456-9\n"
    )
    page.insert_text((72, 72), text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()


class TestPDFDateRedaction:
    """Tests para la ofuscación de fechas en PDFs generados."""

    def test_should_redact_dates_in_simple_pdf(self, tmp_path: Path) -> None:
        """Las fechas deben ser ofuscadas en un PDF simple."""
        pdf_path = str(tmp_path / "test_fechas.pdf")
        output_dir = str(tmp_path / "ofuscados")

        _create_test_pdf_with_dates(pdf_path)

        config = TypeConfig(fecha=True, dni=True, cuit_cuil=True)
        engine = _make_engine(config)
        processor = PDFProcessor(output_dir=output_dir, ner_engine=engine)

        result = processor.process_file(pdf_path)

        assert result.success is True
        assert result.entities_found > 0
        # Debe haber detectado al menos 4 fechas
        assert result.entities_by_type.get("FECHA", 0) >= 4

    def test_should_redact_dates_not_as_dni(self, tmp_path: Path) -> None:
        """Fechas con / no deben ser clasificadas como DNI."""
        pdf_path = str(tmp_path / "test_conflict.pdf")
        output_dir = str(tmp_path / "ofuscados")

        _create_test_pdf_with_dates(pdf_path)

        config = TypeConfig(fecha=True, dni=True)
        engine = _make_engine(config)
        processor = PDFProcessor(output_dir=output_dir, ner_engine=engine)

        result = processor.process_file(pdf_path)

        assert result.success is True
        # Las fechas no deben aparecer como DNI
        fecha_count = result.entities_by_type.get("FECHA", 0)
        assert fecha_count >= 4, (
            f"Esperaba >=4 fechas detectadas, encontró {fecha_count}. "
            f"Distribución: {result.entities_by_type}"
        )

    def test_should_produce_redacted_pdf_with_fecha_labels(
        self, tmp_path: Path
    ) -> None:
        """El PDF ofuscado debe contener etiquetas [FECHA]."""
        pdf_path = str(tmp_path / "test_output.pdf")
        output_dir = str(tmp_path / "ofuscados")

        _create_test_pdf_with_dates(pdf_path)

        config = TypeConfig(fecha=True, dni=True, cuit_cuil=True)
        engine = _make_engine(config)
        processor = PDFProcessor(output_dir=output_dir, ner_engine=engine)

        result = processor.process_file(pdf_path)
        assert result.success is True

        # Verificar que el PDF de salida contiene [FECHA]
        output_path = result.output_file
        assert Path(output_path).exists()

        doc = fitz.open(output_path)
        page = doc[0]
        page_text = page.get_text()
        doc.close()

        assert "[FECHA]" in page_text, (
            f"El PDF ofuscado no contiene [FECHA]. "
            f"Texto encontrado: {page_text[:500]}"
        )


class TestSearchDateFragments:
    """Tests unitarios para _search_date_fragments."""

    def test_should_return_empty_when_not_fecha_type(
        self, tmp_path: Path
    ) -> None:
        """No debe buscar fragmentos si la entidad no es FECHA."""
        config = TypeConfig()
        engine = _make_engine(config)
        processor = PDFProcessor(
            output_dir=str(tmp_path), ner_engine=engine
        )

        entity = DetectedEntity(
            text="35.123.456",
            entity_type=SensitiveDataType.DNI,
            start=0,
            end=10,
            confidence=0.95,
            page=0,
        )

        # Crear un PDF de prueba
        pdf_path = str(tmp_path / "dummy.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "35.123.456", fontsize=11)
        doc.save(pdf_path)
        doc.close()

        doc = fitz.open(pdf_path)
        page = doc[0]

        result = processor._search_date_fragments(page, entity)
        doc.close()

        assert result == []

    def test_should_find_fecha_when_text_exists_in_page(
        self, tmp_path: Path
    ) -> None:
        """Debe encontrar la fecha cuando existe como texto unido en la página."""
        config = TypeConfig()
        engine = _make_engine(config)
        processor = PDFProcessor(
            output_dir=str(tmp_path), ner_engine=engine
        )

        entity = DetectedEntity(
            text="18/11/25",
            entity_type=SensitiveDataType.FECHA,
            start=0,
            end=8,
            confidence=0.95,
            page=0,
        )

        pdf_path = str(tmp_path / "fecha.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Facturación 18/11/25", fontsize=11)
        doc.save(pdf_path)
        doc.close()

        doc = fitz.open(pdf_path)
        page = doc[0]

        result = processor._search_date_fragments(page, entity)
        doc.close()

        assert len(result) >= 1

    def test_should_return_empty_for_non_fecha_format(
        self, tmp_path: Path
    ) -> None:
        """No debe buscar si el texto no tiene formato de fecha."""
        config = TypeConfig()
        engine = _make_engine(config)
        processor = PDFProcessor(
            output_dir=str(tmp_path), ner_engine=engine
        )

        entity = DetectedEntity(
            text="hola mundo",
            entity_type=SensitiveDataType.FECHA,
            start=0,
            end=10,
            confidence=0.95,
            page=0,
        )

        pdf_path = str(tmp_path / "nofecha.pdf")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "hola mundo", fontsize=11)
        doc.save(pdf_path)
        doc.close()

        doc = fitz.open(pdf_path)
        page = doc[0]

        result = processor._search_date_fragments(page, entity)
        doc.close()

        assert result == []
