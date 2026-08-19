"""Receipt API endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.api.deps import get_receipt_service
from app.api.schemas import (
    ConfirmRequest,
    ReceiptDetailOut,
    ReceiptItemOut,
    ReceiptListOut,
    ReceiptOut,
    ReceiptPatch,
    ReceiptTotalsOut,
    TaxDetailOut,
)
from app.domain.models import DomainReceiptItem, DomainReceiptTotals
from app.services.file_service import save_upload
from app.services.receipt_service import ReceiptService

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])


# ---------------------------------------------------------------------------
# Helper converters
# ---------------------------------------------------------------------------

def _item_to_out(item: DomainReceiptItem) -> ReceiptItemOut:
    return ReceiptItemOut(
        id=str(item.id),
        position=item.position,
        raw_description=item.raw_description,
        normalized_description=item.normalized_description,
        quantity=item.quantity,
        unit=item.unit,
        unit_price=item.unit_price,
        price_per_kg=item.price_per_kg,
        discount=item.discount,
        total_price=item.total_price,
        confidence=item.confidence,
        needs_review=item.needs_review,
        line_valid=item.line_valid,
        line_difference=item.line_difference,
    )


def _totals_to_out(totals: DomainReceiptTotals | None) -> ReceiptTotalsOut | None:
    if totals is None:
        return None
    return ReceiptTotalsOut(
        subtotal=totals.subtotal,
        taxes=[
            TaxDetailOut(name=t.name, rate=t.rate, base=t.base, amount=t.amount)
            for t in totals.taxes
        ],
        total=totals.total,
        calculated_total=totals.calculated_total,
        difference=totals.difference,
        totals_valid=totals.totals_valid,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ReceiptOut,
    status_code=201,
    summary="Subir imagen de ticket",
    responses={
        201: {"description": "Ticket creado con estado 'uploaded'"},
        400: {"description": "Fichero inválido (tipo, tamaño o contenido)"},
    },
)
async def upload_receipt(
    file: UploadFile = File(..., description="Imagen JPEG, PNG o WebP del ticket (máx. 10 MB)"),
    svc: ReceiptService = Depends(get_receipt_service),
) -> ReceiptOut:
    """Upload a supermarket receipt image and create a Receipt record."""
    filename, file_path = await save_upload(file)
    receipt = svc.create_receipt(filename, file_path)
    return ReceiptOut(
        id=str(receipt.id),
        filename=receipt.filename,
        status=receipt.status.value,
        commerce=receipt.commerce,
        date=receipt.date,
        time=receipt.time,
        currency=receipt.currency,
        ticket_number=receipt.ticket_number,
        payment_method=receipt.payment_method,
        error_message=receipt.error_message,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
    )


@router.post(
    "/{receipt_id}/process",
    response_model=ReceiptDetailOut,
    summary="Procesar ticket con Gemini",
    responses={
        200: {"description": "Extracción completada"},
        404: {"description": "Ticket no encontrado"},
        409: {"description": "El ticket no está en estado procesable"},
        422: {"description": "Error durante el procesamiento"},
    },
)
def process_receipt(
    receipt_id: str,
    svc: ReceiptService = Depends(get_receipt_service),
) -> ReceiptDetailOut:
    """Trigger synchronous extraction workflow for an uploaded receipt."""
    receipt = svc.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    try:
        receipt = svc.process_receipt(receipt_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Error de procesamiento: {exc}")

    items = svc.get_items(receipt_id)
    totals = svc.get_totals(receipt_id)

    return ReceiptDetailOut(
        id=str(receipt.id),
        filename=receipt.filename,
        status=receipt.status.value,
        commerce=receipt.commerce,
        date=receipt.date,
        time=receipt.time,
        currency=receipt.currency,
        ticket_number=receipt.ticket_number,
        payment_method=receipt.payment_method,
        error_message=receipt.error_message,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
        items=[_item_to_out(i) for i in items],
        totals=_totals_to_out(totals),
    )


@router.get(
    "",
    response_model=ReceiptListOut,
    summary="Listar tickets procesados",
)
def list_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: ReceiptService = Depends(get_receipt_service),
) -> ReceiptListOut:
    receipts = svc.list_receipts(skip=skip, limit=limit)
    items_out = [
        ReceiptOut(
            id=str(r.id),
            filename=r.filename,
            status=r.status.value,
            commerce=r.commerce,
            date=r.date,
            time=r.time,
            currency=r.currency,
            ticket_number=r.ticket_number,
            payment_method=r.payment_method,
            error_message=r.error_message,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in receipts
    ]
    return ReceiptListOut(items=items_out, total=len(items_out), skip=skip, limit=limit)


@router.get(
    "/{receipt_id}",
    response_model=ReceiptDetailOut,
    summary="Detalle de un ticket",
    responses={404: {"description": "Ticket no encontrado"}},
)
def get_receipt(
    receipt_id: str,
    svc: ReceiptService = Depends(get_receipt_service),
) -> ReceiptDetailOut:
    receipt = svc.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    items = svc.get_items(receipt_id)
    totals = svc.get_totals(receipt_id)

    return ReceiptDetailOut(
        id=str(receipt.id),
        filename=receipt.filename,
        status=receipt.status.value,
        commerce=receipt.commerce,
        date=receipt.date,
        time=receipt.time,
        currency=receipt.currency,
        ticket_number=receipt.ticket_number,
        payment_method=receipt.payment_method,
        error_message=receipt.error_message,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
        items=[_item_to_out(i) for i in items],
        totals=_totals_to_out(totals),
    )


@router.patch(
    "/{receipt_id}",
    response_model=ReceiptDetailOut,
    summary="Actualizar campos de un ticket (edición inline)",
    responses={404: {"description": "Ticket no encontrado"}},
)
def patch_receipt(
    receipt_id: str,
    body: ReceiptPatch,
    svc: ReceiptService = Depends(get_receipt_service),
) -> ReceiptDetailOut:
    receipt = svc.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    patch_dict = body.model_dump(exclude_none=True, exclude={"items"})
    receipt = svc.patch_receipt(receipt_id, patch_dict)

    items = svc.get_items(receipt_id)
    totals = svc.get_totals(receipt_id)

    return ReceiptDetailOut(
        id=str(receipt.id),
        filename=receipt.filename,
        status=receipt.status.value,
        commerce=receipt.commerce,
        date=receipt.date,
        time=receipt.time,
        currency=receipt.currency,
        ticket_number=receipt.ticket_number,
        payment_method=receipt.payment_method,
        error_message=receipt.error_message,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
        items=[_item_to_out(i) for i in items],
        totals=_totals_to_out(totals),
    )


@router.post(
    "/{receipt_id}/confirm",
    response_model=ReceiptDetailOut,
    summary="Confirmar ticket revisado",
    responses={
        200: {"description": "Ticket confirmado"},
        404: {"description": "Ticket no encontrado"},
        409: {"description": "El ticket no está en un estado confirmable"},
    },
)
def confirm_receipt(
    receipt_id: str,
    body: ConfirmRequest,
    svc: ReceiptService = Depends(get_receipt_service),
) -> ReceiptDetailOut:
    receipt = svc.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    corrections_json = json.dumps(body.corrections) if body.corrections else None

    try:
        receipt = svc.confirm_receipt(receipt_id, corrections_json)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    items = svc.get_items(receipt_id)
    totals = svc.get_totals(receipt_id)

    return ReceiptDetailOut(
        id=str(receipt.id),
        filename=receipt.filename,
        status=receipt.status.value,
        commerce=receipt.commerce,
        date=receipt.date,
        time=receipt.time,
        currency=receipt.currency,
        ticket_number=receipt.ticket_number,
        payment_method=receipt.payment_method,
        error_message=receipt.error_message,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
        items=[_item_to_out(i) for i in items],
        totals=_totals_to_out(totals),
    )
