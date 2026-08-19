# Receipt Reader MVP

Aplicación web para leer y validar tickets de supermercado españoles mediante visión por computadora con Google Gemini.

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | SvelteKit + TypeScript |
| Backend | FastAPI + Python 3.13 |
| IA | Gemini 1.5 Pro (LangChain) |
| Workflow | LangGraph |
| Validación | Pydantic v2 |
| Base de datos | SQLite |
| Tests backend | Pytest |
| Tests frontend | Playwright |

## Instalación rápida

### Requisitos

- Python 3.12+ (probado con 3.13)
- Node.js 20+
- Clave de API de Google Gemini ([obtener aquí](https://aistudio.google.com/app/apikey))

### Pasos

```bash
# 1. Clonar y entrar al directorio
cd ticket-smart-comparator

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env y poner tu GOOGLE_API_KEY

# 3. Instalar dependencias
make install

# 4. Crear directorio de datos
mkdir -p data/uploads

# 5. Arrancar backend
make dev-backend   # http://localhost:8000

# 6. Arrancar frontend (otra terminal)
make dev-frontend  # http://localhost:5173
```

## Uso

1. Abre `http://localhost:5173`
2. Arrastra o selecciona una imagen de ticket (JPEG, PNG, WebP, máx. 10 MB)
3. El sistema sube la imagen, la envía a Gemini y extrae los productos
4. Revisa la tabla de artículos y los totales
5. Si hay discrepancias matemáticas, aparecerá una alerta
6. Corrige los valores si es necesario y pulsa "Confirmar ticket"

## API

Documentación interactiva disponible en `http://localhost:8000/docs`

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| POST | `/api/v1/receipts` | Subir imagen de ticket |
| POST | `/api/v1/receipts/{id}/process` | Procesar con Gemini |
| GET | `/api/v1/receipts` | Listar tickets |
| GET | `/api/v1/receipts/{id}` | Detalle de ticket |
| PATCH | `/api/v1/receipts/{id}` | Actualizar campos |
| POST | `/api/v1/receipts/{id}/confirm` | Confirmar ticket |

## Tests

```bash
# Tests unitarios + integración del backend
make test-backend

# Tests con cobertura
make test-backend-cov

# Tests E2E (requiere backend y frontend arrancados)
make test-frontend
```

## Estructura del proyecto

```
ticket-smart-comparator/
├── backend/
│   ├── app/
│   │   ├── domain/          # Modelos de dominio puros (sin dependencias de framework)
│   │   ├── extraction/      # Esquemas Pydantic + validación matemática
│   │   ├── persistence/     # SQLAlchemy + repositorios
│   │   ├── workflow/        # LangGraph (nodos + grafo)
│   │   ├── api/             # FastAPI routes + schemas
│   │   ├── services/        # Servicio de aplicación
│   │   ├── config.py
│   │   └── main.py
│   └── tests/
│       ├── unit/            # Tests de validación y dominio
│       ├── integration/     # Tests de API y workflow
│       └── fixtures/        # FakeExtractor + datos demo
├── frontend/
│   └── src/
│       ├── lib/             # API client, tipos, componentes
│       └── routes/          # Páginas SvelteKit
├── data/
│   └── uploads/             # Imágenes subidas (no se versiona)
├── .env.example
├── Makefile
└── docker-compose.yml
```

## Flujo del workflow (LangGraph)

```
load_receipt → normalize_image → extract_receipt → validate_extraction
    → validate_totals → route_result → persist_result
```

Cada nodo recibe y retorna el estado completo. Si cualquier nodo falla, el workflow
salta directamente a `persist_result` marcando el ticket como `failed`.

## Estados del ticket

```
uploaded → processing → extracted → confirmed
                     ↘ needs_review ↗
              ↘ failed
```

## Limitaciones conocidas

1. **Checkpointer no persistente**: El workflow LangGraph usa `MemorySaver` (en memoria).
   El estado del workflow se pierde al reiniciar el servidor. Para persistencia real,
   sustituir por `SqliteSaver` en `backend/app/workflow/graph.py`.

2. **Procesamiento síncrono**: El endpoint `/process` bloquea hasta que Gemini responde
   (~5-15 segundos). En producción, migrar a una cola de tareas (Celery, ARQ, etc.).

3. **Sin autenticación**: MVP sin sistema de usuarios. No desplegar en producción sin añadir auth.

4. **SQLite**: No apto para múltiples escrituras concurrentes. Migrar a PostgreSQL para producción.

5. **Edición inline limitada**: La tabla permite editar descripción, cantidad y unidad, pero los
   recálculos matemáticos no se actualizan en tiempo real en el frontend.

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Clave API de Google Gemini | (requerida) |
| `GEMINI_MODEL` | Modelo a usar | `gemini-1.5-pro` |
| `DATABASE_URL` | URL de SQLite | `sqlite:///./data/receipt_reader.db` |
| `UPLOAD_DIR` | Directorio de uploads | `data/uploads` |
| `MAX_UPLOAD_SIZE_BYTES` | Límite de tamaño | `10485760` (10 MB) |
| `TOTALS_TOLERANCE_EUR` | Tolerancia en totales | `0.02` |
| `LINE_TOLERANCE_EUR` | Tolerancia por línea | `0.01` |

## Privacidad

- Las imágenes se almacenan localmente en `data/uploads/`
- No se registran imágenes ni datos de pago en los logs
- No se almacenan números de tarjeta ni PIN
