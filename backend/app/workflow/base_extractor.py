"""Abstract base for receipt extractors.

Lives in the workflow package so nodes depend on an interface, not a
 concrete LLM implementation.  The concrete LLM extractor lives in
  app/workflow/llm_extractor.py and can be swapped for a fake in tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.extraction.schemas import ReceiptExtractionSchema


class BaseExtractor(ABC):
    """Contract for receipt extraction."""

    @abstractmethod
    def extract(self, image_bytes: bytes, mime_type: str) -> ReceiptExtractionSchema:
        """Extract structured data from an image.

        Must NOT invent values absent from the ticket.
        Must return null for fields that cannot be read.
        """
