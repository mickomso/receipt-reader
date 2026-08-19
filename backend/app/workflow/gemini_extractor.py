"""Gemini multimodal extractor using LangChain with_structured_output."""

from __future__ import annotations

import base64
import logging

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.extraction.schemas import ReceiptExtractionSchema
from app.workflow.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Eres un extractor experto de tickets de supermercado españoles.

REGLAS ESTRICTAS:
1. NUNCA inventes datos que no aparezcan explícitamente en el ticket.
2. Usa null para cualquier campo que no esté presente o que sea ilegible.
3. Conserva la descripción original (raw_description) exactamente como aparece en el ticket.
4. Distingue correctamente las unidades: 'ud' para unidades, 'kg' para kilogramos,
   'g' para gramos, 'l' para litros, 'ml' para mililitros.
5. Usa punto decimal (no coma) para todos los importes numéricos.
6. Marca needs_review: true en cualquier valor que sea dudoso o ambiguo.
7. Devuelve ÚNICAMENTE la estructura JSON definida, sin texto adicional.
8. La moneda es siempre EUR para tickets españoles.
9. Interpreta los descuentos como valores positivos en EUR.
10. overall_confidence debe reflejar tu seguridad global en la extracción (0-1).
"""


class GeminiExtractor(BaseExtractor):
    """Extracts structured receipt data using Google Gemini via LangChain."""

    def __init__(self) -> None:
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            google_api_key=settings.google_api_key,
        )
        self._chain = llm.with_structured_output(ReceiptExtractionSchema)

    def extract(self, image_bytes: bytes, mime_type: str) -> ReceiptExtractionSchema:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": _SYSTEM_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                },
                {
                    "type": "text",
                    "text": (
                        "Extrae toda la información del ticket siguiendo estrictamente "
                        "el esquema JSON proporcionado."
                    ),
                },
            ]
        )
        logger.info("Calling Gemini for extraction (mime=%s, size=%d)", mime_type, len(image_bytes))
        result = self._chain.invoke([message])
        return result
