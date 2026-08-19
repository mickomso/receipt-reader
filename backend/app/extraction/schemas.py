"""Pydantic schemas for the structured output produced by the LLM.

These are the contracts between the LLM extraction step and the rest of the
application.  They MUST NOT import FastAPI, SQLAlchemy, or LangChain.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class TaxDetailSchema(BaseModel):
    """A single tax bracket as extracted from the ticket."""

    name: str | None = Field(None, description="Nombre del impuesto, p.ej. 'IVA 21%'")
    rate: Decimal | None = Field(None, description="Tipo impositivo como decimal, p.ej. 0.21")
    base: Decimal | None = Field(None, description="Base imponible en EUR")
    amount: Decimal | None = Field(None, description="Importe del impuesto en EUR")


class ReceiptItemSchema(BaseModel):
    """One product line from the ticket."""

    raw_description: str = Field(..., description="Descripción literal del ticket sin modificar")
    normalized_description: str | None = Field(
        None, description="Descripción normalizada y legible del producto"
    )
    quantity: Decimal | None = Field(
        None, description="Cantidad del producto (número de unidades, peso en kg o volumen en l)"
    )
    unit: str | None = Field(
        None,
        description=(
            "Unidad de medida: 'ud' para unidades, 'kg' para kilogramos, 'g' para gramos, "
            "'l' para litros, 'ml' para mililitros. Null si no aparece."
        ),
    )
    unit_price: Decimal | None = Field(
        None, description="Precio por unidad en EUR. Null si no aparece."
    )
    price_per_kg: Decimal | None = Field(
        None,
        description=(
            "Precio por kilogramo o litro en EUR para productos a granel. "
            "Null si no aplica."
        ),
    )
    discount: Decimal | None = Field(
        None, description="Descuento aplicado en EUR (valor positivo). Null si no hay descuento."
    )
    total_price: Decimal | None = Field(
        None, description="Importe total de la línea en EUR. Null si no aparece."
    )
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] | None = Field(
        None, description="Confianza en la extracción de esta línea entre 0 y 1."
    )
    needs_review: bool = Field(
        False,
        description=(
            "True si algún valor de esta línea es ambiguo, ilegible o inconsistente."
        ),
    )

    @field_validator("unit")
    @classmethod
    def normalise_unit(cls, v: str | None) -> str | None:
        if v is None:
            return None
        mapping = {
            "unidad": "ud",
            "unidades": "ud",
            "u": "ud",
            "kilogramo": "kg",
            "kilogramos": "kg",
            "kilo": "kg",
            "gramo": "g",
            "gramos": "g",
            "litro": "l",
            "litros": "l",
            "mililitro": "ml",
            "mililitros": "ml",
        }
        return mapping.get(v.lower().strip(), v.lower().strip())


class ReceiptExtractionSchema(BaseModel):
    """Full structured output of the receipt extraction workflow.

    All monetary values use Decimal.
    Null means the value was not present or not legible in the ticket.
    """

    commerce: str | None = Field(None, description="Nombre del comercio o supermercado")
    date: str | None = Field(
        None, description="Fecha del ticket en formato ISO yyyy-mm-dd. Null si no aparece."
    )
    time: str | None = Field(
        None, description="Hora del ticket en formato HH:MM. Null si no aparece."
    )
    currency: str = Field("EUR", description="Moneda, siempre EUR para tickets españoles")
    ticket_number: str | None = Field(
        None, description="Número o referencia del ticket. Null si no aparece."
    )
    items: list[ReceiptItemSchema] = Field(
        default_factory=list, description="Lista de productos del ticket"
    )
    subtotal: Decimal | None = Field(
        None, description="Subtotal antes de impuestos en EUR. Null si no aparece."
    )
    taxes: list[TaxDetailSchema] = Field(
        default_factory=list, description="Desglose de impuestos"
    )
    total: Decimal | None = Field(
        None, description="Total del ticket en EUR. Null si no aparece."
    )
    payment_method: str | None = Field(
        None, description="Método de pago si aparece en el ticket. Null si no aparece."
    )
    overall_confidence: Annotated[float, Field(ge=0.0, le=1.0)] | None = Field(
        None, description="Confianza global de la extracción entre 0 y 1"
    )
    needs_review: bool = Field(
        False,
        description="True si el ticket en conjunto requiere revisión humana",
    )
