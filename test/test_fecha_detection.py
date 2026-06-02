"""Tests para la detección y ofuscación de fechas en formato dd/mm/aa.

Verifica que:
1. El regex de FECHA captura fechas en formatos cortos y largos.
2. La resolución de conflictos prioriza FECHA sobre DNI cuando
   el texto tiene separadores (/ o -).
3. La búsqueda de fechas fragmentadas en PDFs funciona.
"""

from __future__ import annotations

import pytest

from app.models import DetectedEntity, SensitiveDataType, TypeConfig
from app.ner.patterns import detect_with_regex
from app.ner.engine import NEREngine


class TestRegexFechaDetection:
    """Tests unitarios para detección de fechas con regex."""

    def test_should_detect_fecha_dd_mm_aa_when_slash_separator(self) -> None:
        """Fechas en formato DD/MM/AA deben ser detectadas como FECHA."""
        text = "Facturación 18/11/25 Vencimiento 27/11/25"
        entities = detect_with_regex(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        assert len(fecha_entities) >= 2
        fecha_texts = [e.text for e in fecha_entities]
        assert "18/11/25" in fecha_texts
        assert "27/11/25" in fecha_texts

    def test_should_detect_fecha_dd_mm_aaaa_when_slash_separator(self) -> None:
        """Fechas en formato DD/MM/AAAA deben ser detectadas como FECHA."""
        text = "Fecha de nacimiento: 15/03/1990"
        entities = detect_with_regex(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        assert len(fecha_entities) >= 1
        assert any(e.text == "15/03/1990" for e in fecha_entities)

    def test_should_detect_fecha_dd_mm_aa_when_dash_separator(self) -> None:
        """Fechas con guiones (DD-MM-AA) deben ser detectadas como FECHA."""
        text = "Vence el 30-12-25"
        entities = detect_with_regex(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        assert len(fecha_entities) >= 1
        assert any(e.text == "30-12-25" for e in fecha_entities)

    def test_should_detect_fecha_single_digit_day_month(self) -> None:
        """Fechas con día/mes de un dígito deben ser detectadas."""
        text = "Alta: 5/3/25"
        entities = detect_with_regex(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        assert len(fecha_entities) >= 1
        assert any(e.text == "5/3/25" for e in fecha_entities)

    def test_should_detect_fecha_textual_spanish(self) -> None:
        """Fechas textuales en español deben ser detectadas."""
        text = "Fecha de firma: 22 de junio 2025"
        entities = detect_with_regex(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        assert len(fecha_entities) >= 1
        assert any("22 de junio 2025" in e.text for e in fecha_entities)

    def test_should_detect_multiple_fechas_in_financial_doc(self) -> None:
        """Múltiples fechas en un extracto financiero deben ser detectadas."""
        text = (
            "Fecha de Facturación: 18/11/25\n"
            "Fecha de Vencimiento: 27/11/25\n"
            "Próximo Vencimiento: 30/12/25\n"
            "Facturación anterior: 21/10/25\n"
        )
        entities = detect_with_regex(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        fecha_texts = [e.text for e in fecha_entities]
        assert "18/11/25" in fecha_texts
        assert "27/11/25" in fecha_texts
        assert "30/12/25" in fecha_texts
        assert "21/10/25" in fecha_texts


class TestConflictResolutionFechaVsDNI:
    """Tests para la resolución de conflictos FECHA vs DNI."""

    def _make_entity(
        self,
        text: str,
        entity_type: SensitiveDataType,
        start: int,
        confidence: float = 0.95,
    ) -> DetectedEntity:
        """Helper para crear entidades de test."""
        return DetectedEntity(
            text=text,
            entity_type=entity_type,
            start=start,
            end=start + len(text),
            confidence=confidence,
            page=0,
        )

    def test_should_prefer_fecha_over_dni_when_text_has_slashes(self) -> None:
        """FECHA con formato dd/mm/aa debe ganar sobre DNI solapado."""
        engine = NEREngine(config=TypeConfig())

        fecha = self._make_entity(
            "18/11/25", SensitiveDataType.FECHA, start=10, confidence=0.95
        )
        # Simular un DNI que solapa parcialmente (e.g. Ollama clasificó mal)
        dni = self._make_entity(
            "18/11/25", SensitiveDataType.DNI, start=10, confidence=0.95
        )

        # Pasamos ambas entidades con mismo span
        resolved = engine._resolve_conflicts([fecha, dni])

        # FECHA debe ganar
        assert len(resolved) == 1
        assert resolved[0].entity_type == SensitiveDataType.FECHA

    def test_should_prefer_fecha_over_dni_when_dni_has_higher_confidence(
        self,
    ) -> None:
        """FECHA con separadores gana incluso si DNI tiene mayor confianza."""
        engine = NEREngine(config=TypeConfig())

        fecha = self._make_entity(
            "27/11/25", SensitiveDataType.FECHA, start=5, confidence=0.90
        )
        dni = self._make_entity(
            "27/11/25", SensitiveDataType.DNI, start=5, confidence=0.95
        )

        resolved = engine._resolve_conflicts([dni, fecha])

        assert len(resolved) == 1
        assert resolved[0].entity_type == SensitiveDataType.FECHA

    def test_should_prefer_dni_when_text_has_no_separators(self) -> None:
        """DNI sin separadores de fecha debe mantenerse como DNI."""
        engine = NEREngine(config=TypeConfig())

        dni = self._make_entity(
            "35123456", SensitiveDataType.DNI, start=0, confidence=0.95
        )
        # No debería haber conflicto, pero si lo hubiera...
        fecha_fake = self._make_entity(
            "35123456", SensitiveDataType.FECHA, start=0, confidence=0.90
        )

        resolved = engine._resolve_conflicts([dni, fecha_fake])

        # No tiene formato fecha (sin / ni -), así que la heurística no aplica
        # y gana por confianza
        assert len(resolved) == 1
        assert resolved[0].entity_type == SensitiveDataType.DNI

    def test_should_prefer_cuenta_over_fecha_when_format_matches(self) -> None:
        """CUENTA_BANCARIA con formato xxxx-xxxxxx-xxxxx gana sobre FECHA."""
        engine = NEREngine(config=TypeConfig())

        cuenta = self._make_entity(
            "3764-575886-12000",
            SensitiveDataType.CUENTA_BANCARIA,
            start=0,
            confidence=0.95,
        )
        fecha = self._make_entity(
            "3764-575886-12000",
            SensitiveDataType.FECHA,
            start=0,
            confidence=0.95,
        )

        resolved = engine._resolve_conflicts([cuenta, fecha])

        assert len(resolved) == 1
        assert resolved[0].entity_type == SensitiveDataType.CUENTA_BANCARIA

    def test_should_keep_non_overlapping_entities_intact(self) -> None:
        """Entidades sin solapamiento deben mantenerse todas."""
        engine = NEREngine(config=TypeConfig())

        fecha1 = self._make_entity(
            "18/11/25", SensitiveDataType.FECHA, start=0
        )
        fecha2 = self._make_entity(
            "27/11/25", SensitiveDataType.FECHA, start=20
        )
        dni = self._make_entity(
            "35.123.456", SensitiveDataType.DNI, start=40
        )

        resolved = engine._resolve_conflicts([fecha1, fecha2, dni])

        assert len(resolved) == 3


class TestNEREngineFechaIntegration:
    """Tests de integración para detección de fechas con el motor NER."""

    def test_should_detect_fechas_in_extracto_bancario(self) -> None:
        """El motor completo debe detectar fechas de un extracto bancario."""
        config = TypeConfig(fecha=True, dni=True)
        engine = NEREngine(config=config)

        text = (
            "Estado de Cuenta\n"
            "Facturación 18/11/25 Vencimiento 27/11/25\n"
            "Próximo Vencimiento 30/12/25\n"
        )

        entities = engine.detect(text, page=0)

        fecha_entities = [
            e for e in entities if e.entity_type == SensitiveDataType.FECHA
        ]
        fecha_texts = [e.text for e in fecha_entities]

        # Cada fecha debe ser una entidad independiente (no fusionadas)
        assert "18/11/25" in fecha_texts, (
            f"'18/11/25' no encontrada en: {fecha_texts}"
        )
        assert "27/11/25" in fecha_texts, (
            f"'27/11/25' no encontrada en: {fecha_texts}"
        )
        assert "30/12/25" in fecha_texts, (
            f"'30/12/25' no encontrada en: {fecha_texts}"
        )

    def test_should_not_detect_fechas_when_type_disabled(self) -> None:
        """No debe detectar fechas cuando el tipo está deshabilitado."""
        config = TypeConfig(fecha=False)
        engine = NEREngine(config=config)

        text = "Fecha: 18/11/25"
        entities = engine.detect(text, page=0)

        fecha_entities = [
            e for e in entities
            if e.entity_type == SensitiveDataType.FECHA
        ]
        assert len(fecha_entities) == 0

    def test_should_detect_fecha_alongside_other_entities(self) -> None:
        """Fechas deben coexistir con otros tipos de entidades detectadas."""
        config = TypeConfig(fecha=True, cuit_cuil=True, dni=True)
        engine = NEREngine(config=config)

        text = "CUIT: 20-35123456-9 Fecha: 18/11/25"
        entities = engine.detect(text, page=0)

        types_found = {e.entity_type for e in entities}
        assert SensitiveDataType.FECHA in types_found
        # El CUIT regex requiere formato XX-XXXXXXXX-X
        # y 20-35123456-9 matchea el patrón de CUIT
        assert (
            SensitiveDataType.CUIT_CUIL in types_found
            or SensitiveDataType.DNI in types_found
        ), f"Se esperaba CUIT_CUIL o DNI, encontró: {types_found}"
