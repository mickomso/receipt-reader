# Receipt Reader MVP

Web application to read and validate Spanish supermarket receipts using computer vision with xAI Grok.

## Stack

| Layer          | Technology             |
| -------------- | ---------------------- |
| Frontend       | SvelteKit + TypeScript |
| Backend        | FastAPI + Python 3.13  |
| AI             | Grok 4.5 (LangChain)   |
| Workflow       | LangGraph              |
| Validation     | Pydantic v2            |
| Database       | SQLite                 |
| Backend tests  | Pytest                 |
| Frontend tests | Playwright             |

## Quick Start

### Requirements

- Python 3.12+ (tested with 3.13)
- Node.js 20+
- xAI API key ([get it here](https://console.x.ai/))

### Steps

```bash
# 1. Clone and enter the directory
cd ticket-smart-comparator

# 2. Copy environment variables
cp .env.example .env
# Edit .env and set your XAI_API_KEY
# Make sure EXTRACTOR_BACKEND=grok

# 3. Install dependencies
make install

# 4. Create data directory
mkdir -p data/uploads

# 5. Start backend
make dev-backend   # http://localhost:8000

# 6. Start frontend (another terminal)
make dev-frontend  # http://localhost:5173
```

## Usage

1. Open `http://localhost:5173`
2. Drag or select a receipt image (JPEG, PNG, WebP, max. 10 MB)
3. The system uploads the image, sends it to Grok, and extracts the products
4. Review the item table and totals
5. If there are mathematical discrepancies, an alert will appear
6. Correct values if needed and click "Confirm receipt"

## API

Interactive documentation is available at `http://localhost:8000/docs`

### Endpoints

| Method | Route                           | Description          |
| ------ | ------------------------------- | -------------------- |
| GET    | `/health`                       | Service status       |
| POST   | `/api/v1/receipts`              | Upload receipt image |
| POST   | `/api/v1/receipts/{id}/process` | Process with Grok    |
| GET    | `/api/v1/receipts`              | List receipts        |
| GET    | `/api/v1/receipts/{id}`         | Receipt detail       |
| PATCH  | `/api/v1/receipts/{id}`         | Update fields        |
| POST   | `/api/v1/receipts/{id}/confirm` | Confirm receipt      |

## Tests

```bash
# Backend unit + integration tests
make test-backend

# Backend tests with coverage
make test-backend-cov

# E2E tests (requires backend and frontend running)
make test-frontend
```

## Project Structure

```
ticket-smart-comparator/
├── backend/
│   ├── app/
│   │   ├── domain/          # Pure domain models (no framework dependencies)
│   │   ├── extraction/      # Pydantic schemas + mathematical validation
│   │   ├── persistence/     # SQLAlchemy + repositories
│   │   ├── workflow/        # LangGraph (nodes + graph)
│   │   ├── api/             # FastAPI routes + schemas
│   │   ├── services/        # Application service
│   │   ├── config.py
│   │   └── main.py
│   └── tests/
│       ├── unit/            # Validation and domain tests
│       ├── integration/     # API and workflow tests
│       └── fixtures/        # FakeExtractor + demo data
├── frontend/
│   └── src/
│       ├── lib/             # API client, types, components
│       └── routes/          # SvelteKit pages
├── data/
│   └── uploads/             # Uploaded images (not versioned)
├── .env.example
├── Makefile
└── docker-compose.yml
```

## Workflow Flow (LangGraph)

```
load_receipt → normalize_image → extract_receipt → validate_extraction
    → validate_totals → route_result → persist_result
```

Each node receives and returns the full state. If any node fails, the workflow
jumps directly to `persist_result`, marking the receipt as `failed`.

## Receipt States

```
uploaded → processing → extracted → confirmed
                     ↘ needs_review ↗
              ↘ failed
```

## Known Limitations

1. **Non-persistent checkpointer**: The LangGraph workflow uses `MemorySaver` (in-memory).
   Workflow state is lost when the server restarts. For real persistence,
   replace it with `SqliteSaver` in `backend/app/workflow/graph.py`.

2. **Synchronous processing**: The `/process` endpoint blocks until Grok responds
   (~5-15 seconds). In production, migrate to a task queue (Celery, ARQ, etc.).

3. **No authentication**: This MVP has no user system. Do not deploy to production without adding auth.

4. **SQLite**: Not suitable for multiple concurrent writes. Migrate to PostgreSQL for production.

5. **Limited inline editing**: The table allows editing description, quantity, and unit, but
   mathematical recalculations are not updated in real time on the frontend.

## Environment Variables

| Variable                | Description                            | Default                              |
| ----------------------- | -------------------------------------- | ------------------------------------ |
| `XAI_API_KEY`           | xAI API key                            | (required)                           |
| `GROK_MODEL`            | Model to use                           | `grok-4.5`                           |
| `EXTRACTOR_BACKEND`     | Extractor backend (`grok` or `gemini`) | `grok`                               |
| `DATABASE_URL`          | SQLite URL                             | `sqlite:///./data/receipt_reader.db` |
| `UPLOAD_DIR`            | Upload directory                       | `data/uploads`                       |
| `MAX_UPLOAD_SIZE_BYTES` | Size limit                             | `10485760` (10 MB)                   |
| `TOTALS_TOLERANCE_EUR`  | Totals tolerance                       | `0.02`                               |
| `LINE_TOLERANCE_EUR`    | Per-line tolerance                     | `0.01`                               |

## Privacy

- Images are stored locally in `data/uploads/`
- Images and payment data are not logged
- Card numbers and PINs are not stored
