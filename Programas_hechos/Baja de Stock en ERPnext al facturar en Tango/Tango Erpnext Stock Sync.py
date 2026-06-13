"""
Sistema Industrial - Tango -> ERPNext Stock Sync MVP

Objetivo:
- Consultar movimientos de stock generados por facturación en Tango API Live Query.
- Normalizar cada renglón como evento de stock.
- Evitar reprocesar dos veces el mismo movimiento usando SQLite.
- Enviar el movimiento a ERPNext mediante Stock Entry.

Instalación:
    py -m pip install fastapi uvicorn httpx pydantic pydantic-settings python-dotenv

Ejecución:
    uvicorn tango_erpnext_stock_sync:app --reload --port 8010

Archivo .env esperado:
    TANGO_API_BASE_URL=http://server-t:17000
    TANGO_API_AUTHORIZATION=CAMBIAR_TOKEN
    TANGO_COMPANY=25
    TANGO_PROCESS=12567

    ERPNEXT_BASE_URL=http://erpnext.localhost:8000
    ERPNEXT_API_KEY=CAMBIAR_API_KEY
    ERPNEXT_API_SECRET=CAMBIAR_API_SECRET
    ERPNEXT_SOURCE_WAREHOUSE=Stores - SI
    ERPNEXT_TARGET_WAREHOUSE=Stores - SI

Notas:
- Para facturas, Tango devuelve CANTIDAD_CONTROL_STOCK negativa. Eso se transforma en stock_out.
- Para notas de crédito, Tango devuelve CANTIDAD_CONTROL_STOCK positiva. Eso se transforma en stock_in.
- El primer MVP usa Stock Entry en ERPNext.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DB_PATH = Path("tango_erpnext_sync.sqlite3")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    tango_api_base_url: str = Field(..., alias="TANGO_API_BASE_URL")
    tango_api_authorization: str = Field(..., alias="TANGO_API_AUTHORIZATION")
    tango_company: str = Field(..., alias="TANGO_COMPANY")
    tango_process: int = Field(..., alias="TANGO_PROCESS")

    erpnext_base_url: str = Field(..., alias="ERPNEXT_BASE_URL")
    erpnext_api_key: str = Field(..., alias="ERPNEXT_API_KEY")
    erpnext_api_secret: str = Field(..., alias="ERPNEXT_API_SECRET")
    erpnext_source_warehouse: str = Field(..., alias="ERPNEXT_SOURCE_WAREHOUSE")
    erpnext_target_warehouse: str = Field(..., alias="ERPNEXT_TARGET_WAREHOUSE")


settings = Settings()

app = FastAPI(
    title="Sistema Industrial - Tango ERPNext Stock Sync",
    version="0.1.0",
)


class MovementType(str, Enum):
    STOCK_OUT = "stock_out"
    STOCK_IN = "stock_in"
    ZERO = "zero"


class SyncStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    ERROR = "error"
    SKIPPED = "skipped"


class TangoRawMovement(BaseModel):
    ID_STA11: int
    ID_STA14: int
    ID_GVA12: Optional[int] = None
    ID_CPA04: Optional[int] = None
    FECHA_DE_COMPROBANTE: datetime
    ORIGEN_DEL_MOVIMIENTO: str
    TIPO_COMPROBANTE: str
    NRO_COMPROBANTE: str
    COMPROBANTE: str
    COD_ARTICULO: str
    DESC_ARTICULO: str
    TIPO_INTERNO_STOCK: str
    NRO_INTERNO_STOCK: str
    UM_CONTROL_STOCK: str
    CANTIDAD_CONTROL_STOCK: Decimal
    TIPO_INTERNO: Optional[str] = None
    NRO_INTERNO: Optional[str] = None


class StockMovement(BaseModel):
    external_id: str
    source_system: str = "tango"
    document_id: Optional[int]
    document_type: str
    document_number: str
    stock_internal_number: str
    item_id: int
    item_code: str
    description: str
    unit: str
    signed_quantity: Decimal
    quantity: Decimal
    movement_type: MovementType
    posting_date: date


class SyncResult(BaseModel):
    external_id: str
    document_number: str
    item_code: str
    movement_type: MovementType
    quantity: Decimal
    status: SyncStatus
    erpnext_reference: Optional[str] = None
    error_message: Optional[str] = None


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_log (
                external_id TEXT PRIMARY KEY,
                document_number TEXT NOT NULL,
                item_code TEXT NOT NULL,
                signed_quantity TEXT NOT NULL,
                status TEXT NOT NULL,
                erpnext_reference TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()


def parse_tango_response(payload: dict[str, Any]) -> list[TangoRawMovement]:
    if not payload.get("succeeded"):
        raise HTTPException(status_code=502, detail={"message": "Tango API no fue exitosa", "payload": payload})

    result_data = payload.get("resultData") or {}
    rows = result_data.get("list") or []
    return [TangoRawMovement.model_validate(row) for row in rows]


def normalize_movement(raw: TangoRawMovement) -> StockMovement:
    signed_qty = raw.CANTIDAD_CONTROL_STOCK

    if signed_qty < 0:
        movement_type = MovementType.STOCK_OUT
        quantity = abs(signed_qty)
    elif signed_qty > 0:
        movement_type = MovementType.STOCK_IN
        quantity = signed_qty
    else:
        movement_type = MovementType.ZERO
        quantity = Decimal("0")

    # Clave idempotente por renglón de movimiento.
    # ID_STA14 = movimiento stock; ID_STA11 = artículo; NRO_INTERNO_STOCK discrimina comprobante interno.
    external_id = f"tango:{raw.ID_STA14}:{raw.ID_STA11}:{raw.NRO_INTERNO_STOCK}"

    return StockMovement(
        external_id=external_id,
        document_id=raw.ID_GVA12,
        document_type=raw.TIPO_COMPROBANTE,
        document_number=raw.NRO_COMPROBANTE,
        stock_internal_number=raw.NRO_INTERNO_STOCK,
        item_id=raw.ID_STA11,
        item_code=raw.COD_ARTICULO.strip(),
        description=raw.DESC_ARTICULO.strip(),
        unit=raw.UM_CONTROL_STOCK.strip(),
        signed_quantity=signed_qty,
        quantity=quantity,
        movement_type=movement_type,
        posting_date=raw.FECHA_DE_COMPROBANTE.date(),
    )


def was_processed(external_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT status FROM sync_log WHERE external_id = ? AND status = ?",
            (external_id, SyncStatus.PROCESSED.value),
        ).fetchone()
    return row is not None


def upsert_log(result: SyncResult) -> None:
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO sync_log (
                external_id, document_number, item_code, signed_quantity, status,
                erpnext_reference, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id) DO UPDATE SET
                status = excluded.status,
                erpnext_reference = excluded.erpnext_reference,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at
            """,
            (
                result.external_id,
                result.document_number,
                result.item_code,
                str(result.quantity),
                result.status.value,
                result.erpnext_reference,
                result.error_message,
                now,
                now,
            ),
        )
        conn.commit()


class TangoLiveQueryClient:
    def __init__(self, base_url: str, api_authorization: str, company: str, process: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_authorization = api_authorization
        self.company = company
        self.process = process

    async def fetch_stock_movements(
        self,
        from_date: str,
        to_date: str,
        page_size: int = 100,
        page_index: int = 0,
        custom_query: str = "0",
    ) -> dict[str, Any]:
        url = f"{self.base_url}/Api/GetApiLiveQueryData"
        headers = {
            "ApiAuthorization": self.api_authorization,
            "Company": self.company,
        }
        params = {
            "process": self.process,
            "fromDate": from_date,
            "toDate": to_date,
            "pageSize": page_size,
            "pageIndex": page_index,
            "customQuery": custom_query,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url, headers=headers, params=params)

        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Error consultando Tango Live Query",
                    "status_code": response.status_code,
                    "body": response.text[:2000],
                },
            )
        return response.json()


class ERPNextClient:
    def __init__(self, base_url: str, api_key: str, api_secret: str, source_warehouse: str, target_warehouse: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.source_warehouse = source_warehouse
        self.target_warehouse = target_warehouse

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
        }

    async def create_stock_entry(self, movement: StockMovement) -> str:
        if movement.movement_type == MovementType.STOCK_OUT:
            stock_entry_type = "Material Issue"
            item_payload = {
                "item_code": movement.item_code,
                "qty": float(movement.quantity),
                "s_warehouse": self.source_warehouse,
            }
        elif movement.movement_type == MovementType.STOCK_IN:
            stock_entry_type = "Material Receipt"
            item_payload = {
                "item_code": movement.item_code,
                "qty": float(movement.quantity),
                "t_warehouse": self.target_warehouse,
            }
        else:
            raise ValueError("Movimiento de stock cero no se envía a ERPNext")

        payload = {
            "doctype": "Stock Entry",
            "stock_entry_type": stock_entry_type,
            "posting_date": movement.posting_date.isoformat(),
            "remarks": (
                f"Sistema Industrial - Tango {movement.document_type} {movement.document_number} "
                f"- movimiento {movement.external_id}"
            ),
            "items": [item_payload],
        }

        url = f"{self.base_url}/api/resource/Stock Entry"
        async with httpx.AsyncClient(timeout=60) as client:
            create_response = await client.post(url, headers=self.headers, json=payload)

        if create_response.status_code >= 400:
            raise RuntimeError(f"ERPNext create Stock Entry error: {create_response.text[:2000]}")

        created = create_response.json().get("data") or {}
        stock_entry_name = created.get("name")
        if not stock_entry_name:
            raise RuntimeError(f"ERPNext no devolvió name: {create_response.text[:2000]}")

        # Submit del Stock Entry para que impacte stock.
        submit_url = f"{self.base_url}/api/resource/Stock Entry/{stock_entry_name}"
        submit_payload = {"docstatus": 1}
        async with httpx.AsyncClient(timeout=60) as client:
            submit_response = await client.put(submit_url, headers=self.headers, json=submit_payload)

        if submit_response.status_code >= 400:
            raise RuntimeError(f"ERPNext submit Stock Entry error: {submit_response.text[:2000]}")

        return stock_entry_name


tango_client = TangoLiveQueryClient(
    base_url=settings.tango_api_base_url,
    api_authorization=settings.tango_api_authorization,
    company=settings.tango_company,
    process=settings.tango_process,
)

erpnext_client = ERPNextClient(
    base_url=settings.erpnext_base_url,
    api_key=settings.erpnext_api_key,
    api_secret=settings.erpnext_api_secret,
    source_warehouse=settings.erpnext_source_warehouse,
    target_warehouse=settings.erpnext_target_warehouse,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "tango-erpnext-stock-sync"}


@app.get("/tango/stock-movements", response_model=list[StockMovement])
async def preview_tango_stock_movements(
    from_date: str = Query(..., description="Formato Tango: dd/MM/yyyy"),
    to_date: str = Query(..., description="Formato Tango: dd/MM/yyyy"),
    page_size: int = Query(default=100, ge=1, le=500),
    page_index: int = Query(default=0, ge=0),
) -> list[StockMovement]:
    payload = await tango_client.fetch_stock_movements(
        from_date=from_date,
        to_date=to_date,
        page_size=page_size,
        page_index=page_index,
    )
    raw_rows = parse_tango_response(payload)
    return [normalize_movement(row) for row in raw_rows]


@app.post("/sync/tango-to-erpnext", response_model=list[SyncResult])
async def sync_tango_to_erpnext(
    from_date: str = Query(..., description="Formato Tango: dd/MM/yyyy"),
    to_date: str = Query(..., description="Formato Tango: dd/MM/yyyy"),
    page_size: int = Query(default=100, ge=1, le=500),
    page_index: int = Query(default=0, ge=0),
    dry_run: bool = Query(default=True, description="True = no impacta ERPNext; False = crea Stock Entry"),
) -> list[SyncResult]:
    payload = await tango_client.fetch_stock_movements(
        from_date=from_date,
        to_date=to_date,
        page_size=page_size,
        page_index=page_index,
    )
    raw_rows = parse_tango_response(payload)
    movements = [normalize_movement(row) for row in raw_rows]

    results: list[SyncResult] = []

    for movement in movements:
        if movement.movement_type == MovementType.ZERO:
            result = SyncResult(
                external_id=movement.external_id,
                document_number=movement.document_number,
                item_code=movement.item_code,
                movement_type=movement.movement_type,
                quantity=movement.quantity,
                status=SyncStatus.SKIPPED,
                error_message="Movimiento con cantidad cero",
            )
            upsert_log(result)
            results.append(result)
            continue

        if was_processed(movement.external_id):
            results.append(
                SyncResult(
                    external_id=movement.external_id,
                    document_number=movement.document_number,
                    item_code=movement.item_code,
                    movement_type=movement.movement_type,
                    quantity=movement.quantity,
                    status=SyncStatus.SKIPPED,
                    error_message="Movimiento ya procesado anteriormente",
                )
            )
            continue

        if dry_run:
            result = SyncResult(
                external_id=movement.external_id,
                document_number=movement.document_number,
                item_code=movement.item_code,
                movement_type=movement.movement_type,
                quantity=movement.quantity,
                status=SyncStatus.PENDING,
                error_message="Dry run: no enviado a ERPNext",
            )
            results.append(result)
            continue

        try:
            erpnext_reference = await erpnext_client.create_stock_entry(movement)
            result = SyncResult(
                external_id=movement.external_id,
                document_number=movement.document_number,
                item_code=movement.item_code,
                movement_type=movement.movement_type,
                quantity=movement.quantity,
                status=SyncStatus.PROCESSED,
                erpnext_reference=erpnext_reference,
            )
        except Exception as exc:
            result = SyncResult(
                external_id=movement.external_id,
                document_number=movement.document_number,
                item_code=movement.item_code,
                movement_type=movement.movement_type,
                quantity=movement.quantity,
                status=SyncStatus.ERROR,
                error_message=str(exc),
            )

        upsert_log(result)
        results.append(result)

    return results


@app.get("/sync/log")
async def get_sync_log(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT external_id, document_number, item_code, signed_quantity, status,
                   erpnext_reference, error_message, created_at, updated_at
            FROM sync_log
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
