# Receipt Reader MVP

Full-stack application for extracting and validating product information from Spanish supermarket receipts using multimodal AI.

Users can upload a receipt image, review the extracted products and totals, correct discrepancies, and confirm the final receipt data.

> **Project status:** Local MVP for technical validation. It is not ready for production deployment.

## Features

- Upload receipt images in JPEG, PNG or WebP format.
- Extract products, quantities, prices and totals using xAI Grok.
- Validate AI-generated output with Pydantic schemas.
- Check mathematical consistency between line items and receipt totals.
- Review and edit extracted data before confirmation.
- Persist receipts and processing results in SQLite.
- Expose interactive OpenAPI/Swagger API documentation.
- Run backend unit and integration tests with Pytest.
- Run frontend end-to-end tests with Playwright.
- Use a deterministic fake extractor in tests.

## Demo

Add a short screen recording or animated GIF here when available.

```markdown
[Watch the demo](docs/demo.mp4)
```

The demo should show:

1. Uploading a Spanish supermarket receipt.
2. Extracting products and totals with Grok.
3. Validating the extracted information.
4. Reviewing and editing the result.
5. Confirming the receipt.

Use anonymized or fictional receipt data in the demo. Do not publish real payment information or personally identifiable data.

## Technology Stack

| Layer               | Technology              | Purpose                                     |
| ------------------- | ----------------------- | ------------------------------------------- |
| Frontend            | SvelteKit, TypeScript   | Receipt upload, review and correction UI    |
| Backend             | FastAPI, Python 3.13    | REST API and application services           |
| AI extraction       | xAI Grok 4.5, LangChain | Multimodal receipt extraction               |
| Workflow            | LangGraph               | Explicit extraction and validation pipeline |
| Validation          | Pydantic v2             | Schema and data validation                  |
| Persistence         | SQLite, SQLAlchemy      | Local receipt storage                       |
| Backend testing     | Pytest                  | Unit and integration testing                |
| Frontend testing    | Playwright              | End-to-end testing                          |
| Local orchestration | Docker Compose, Make    | Development workflow                        |

## Architecture

The backend follows a modular architecture that separates domain logic, application services, infrastructure and API concerns.

```text
receipt-reader/
├── backend/
│   ├── app/
│   │   ├── domain/          # Domain models without framework dependencies
│   │   ├── extraction/      # Pydantic schemas and mathematical validation
│   │   ├── persistence/     # SQLAlchemy models and repositories
│   │   ├── workflow/        # LangGraph nodes and graph definition
│   │   ├── api/             # FastAPI routes and request schemas
│   │   ├── services/        # Application services
│   │   ├── config.py        # Application configuration
│   │   └── main.py          # FastAPI application entry point
│   └── tests/
│       ├── unit/            # Domain and validation tests
│       ├── integration/     # API and workflow tests
│       └── fixtures/        # Fake extractor and demo data
├── frontend/
│   └── src/
│       ├── lib/             # API client, types and components
│       └── routes/          # SvelteKit pages
├── data/
│   └── uploads/             # Uploaded images, not versioned
├── .env.example
├── Makefile
└── docker-compose.yml
```

## Processing Workflow

Receipt processing is represented as an explicit LangGraph workflow:

```text
load_receipt
    ↓
normalize_image
    ↓
extract_receipt
    ↓
validate_extraction
    ↓
validate_totals
    ↓
route_result
    ↓
persist_result
```

Each node receives and returns the complete workflow state.

If a node fails, the workflow moves directly to `persist_result` and marks the receipt as failed.

## Receipt State Flow

```text
uploaded → processing → extracted → confirmed
                         ↘ needs_review ↗
              ↘ failed
```

A receipt may require manual review when the extracted data does not pass schema or mathematical validation.

## Technical Decisions

- **Explicit workflow:** LangGraph models the receipt-processing pipeline as a sequence of independent, observable steps.
- **AI output validation:** Grok output is treated as untrusted input and validated using Pydantic before entering the domain flow.
- **Mathematical validation:** The application checks the relationship between quantities, unit prices, line totals and receipt totals.
- **Modular backend:** Domain logic is kept separate from FastAPI, persistence and external AI integrations.
- **Deterministic tests:** A fake extractor makes workflow and integration tests independent from the external xAI API.
- **Local-first persistence:** SQLite keeps the MVP easy to run without requiring an external database.
- **Human-in-the-loop review:** Users can correct extracted values before confirming the final receipt.

## Quick Start

### Requirements

- Python 3.12 or later.
- Python 3.13 tested.
- Node.js 20 or later.
- An xAI API key.
- GNU Make.
- Optional: Docker and Docker Compose.

Create an API key from the [xAI Console](https://console.x.ai/).

### Installation

Clone the repository and enter the project directory:

```bash
git clone <YOUR_REPOSITORY_URL>
cd receipt-reader
```

Copy the example environment file:

```bash
cp .env.example .env
```

Set the required API key in `.env`:

```dotenv
XAI_API_KEY=<YOUR_XAI_API_KEY>
EXTRACTOR_BACKEND=grok
```

Install the project dependencies:

```bash
make install
```

Create the upload directory:

```bash
mkdir -p data/uploads
```

### Start the backend

Run the backend in one terminal:

```bash
make dev-backend
```

The API will be available at:

```text
http://localhost:8000
```

### Start the frontend

Run the frontend in another terminal:

```bash
make dev-frontend
```

The web application will be available at:

```text
http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Usage

1. Open the frontend application.
2. Drag or select a receipt image.
3. Upload a JPEG, PNG or WebP image up to 10 MB.
4. Wait while the application processes the receipt with Grok.
5. Review the extracted products and totals.
6. Correct any values that require manual adjustment.
7. Confirm the receipt.

If mathematical discrepancies are detected, the application displays a review alert before confirmation.

## API

Interactive API documentation is available at:

- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

### Endpoints

| Method  | Route                           | Description                 |
| ------- | ------------------------------- | --------------------------- |
| `GET`   | `/health`                       | Check service status        |
| `POST`  | `/api/v1/receipts`              | Upload a receipt image      |
| `POST`  | `/api/v1/receipts/{id}/process` | Process a receipt with Grok |
| `GET`   | `/api/v1/receipts`              | List receipts               |
| `GET`   | `/api/v1/receipts/{id}`         | Get receipt details         |
| `PATCH` | `/api/v1/receipts/{id}`         | Update receipt fields       |
| `POST`  | `/api/v1/receipts/{id}/confirm` | Confirm a receipt           |

## Testing

### Backend unit and integration tests

```bash
make test-backend
```

### Backend tests with coverage

```bash
make test-backend-cov
```

### Frontend end-to-end tests

The backend and frontend must be running before executing the end-to-end tests:

```bash
make test-frontend
```

The test suite includes:

- Domain validation tests.
- Mathematical totals validation.
- API integration tests.
- Workflow tests.
- Frontend end-to-end scenarios.

## Configuration

Configuration is loaded through environment variables.

| Variable                | Description                            | Default                              |
| ----------------------- | -------------------------------------- | ------------------------------------ |
| `XAI_API_KEY`           | xAI API key                            | Required                             |
| `GROK_MODEL`            | xAI model used for extraction          | `grok-4.5`                           |
| `EXTRACTOR_BACKEND`     | Extraction backend: `grok` or `gemini` | `grok`                               |
| `DATABASE_URL`          | Database connection URL                | `sqlite:///./data/receipt_reader.db` |
| `UPLOAD_DIR`            | Directory for uploaded images          | `data/uploads`                       |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum upload size                    | `10485760`                           |
| `TOTALS_TOLERANCE_EUR`  | Allowed receipt total difference       | `0.02`                               |
| `LINE_TOLERANCE_EUR`    | Allowed line total difference          | `0.01`                               |

## Security and Privacy

- Receipt images are stored locally in `data/uploads/`.
- Uploaded images are not versioned in Git.
- Images and payment data are not logged.
- Card numbers and PINs are not stored by the application.
- API keys must be provided through environment variables.
- Real receipts should not be uploaded to public demos or shared repositories.
- The application has no authentication and should not be exposed publicly without additional security controls.

## Known Limitations

This MVP is designed for local development and technical validation.

### Non-persistent workflow state

The LangGraph workflow currently uses `MemorySaver`, so workflow state is lost if the backend restarts.

For production use, replace it with a durable checkpointer such as `SqliteSaver` or another persistent implementation.

### Synchronous processing

The `/process` endpoint blocks while waiting for the Grok response. Local processing usually takes several seconds, depending on the image and external API response time.

For production use, move processing to a background task or distributed task queue such as Celery, ARQ or an equivalent solution.

### No authentication

The MVP does not include users, sessions or access control.

Authentication and authorization must be added before exposing the application to multiple users or the public internet.

### SQLite persistence

SQLite is appropriate for local development but is not ideal for multiple concurrent writes or horizontal scaling.

A production deployment should use PostgreSQL or another server-grade database.

### Limited inline editing

The frontend allows editing descriptions, quantities and units, but mathematical recalculations are not updated in real time in the user interface.

### Local file storage

Uploaded images are stored on the local filesystem.

A production deployment should consider object storage, retention policies, encryption and automatic deletion of uploaded images.

## Roadmap

Potential next steps include:

- Add authentication and user-level receipt isolation.
- Move receipt processing to an asynchronous task queue.
- Replace `MemorySaver` with durable workflow checkpoints.
- Migrate from SQLite to PostgreSQL.
- Add object storage for uploaded images.
- Recalculate totals in real time in the frontend.
- Add database migrations.
- Improve error handling and retry policies for AI provider failures.
- Add observability, structured logging and metrics.
- Add receipt anonymization and configurable retention policies.
- Deploy a secured public demo.
- Add support for additional receipt formats and languages.

## Project Status

| Area                      | Status          |
| ------------------------- | --------------- |
| Receipt image upload      | Implemented     |
| AI extraction with Grok   | Implemented     |
| Schema validation         | Implemented     |
| Mathematical validation   | Implemented     |
| Manual review flow        | Implemented     |
| Receipt confirmation      | Implemented     |
| SQLite persistence        | Implemented     |
| Backend tests             | Implemented     |
| Frontend end-to-end tests | Implemented     |
| Authentication            | Not implemented |
| Asynchronous processing   | Not implemented |
| Production deployment     | Not implemented |

## What I Learned

This project was an opportunity to explore:

- Building a full-stack application from an initial idea.
- Using multimodal AI for semi-structured document extraction.
- Designing an explicit workflow with LangGraph.
- Validating AI-generated data before accepting it.
- Separating domain logic from API and persistence concerns.
- Combining unit, integration and end-to-end testing.
- Identifying the architectural gap between a local MVP and a production-ready system.

AI tools were used during development to accelerate exploration and generate initial code. The implementation was subsequently reviewed, adapted and tested as part of the development process.

## License

Add the license for this project here.

For example:

```text
This project is licensed under the MIT License.
```

If the project is not yet licensed, state that clearly instead of including an incomplete license declaration.
