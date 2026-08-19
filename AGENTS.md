# AGENTS.md

## Objetivo

Construir un MVP web para leer tickets de supermercado.

## Stack obligatorio

- Frontend: SvelteKit + TypeScript.
- Backend: FastAPI + Python 3.12.
- IA: Gemini multimodal mediante LangChain.
- Workflow: LangGraph.
- Validación: Pydantic.
- Base de datos MVP: SQLite.
- Test backend: Pytest.
- Test frontend: Playwright.

## Reglas de diseño

- El dominio no puede importar FastAPI, LangChain, LangGraph ni SQLite.
- Todos los importes deben usar Decimal.
- No confiar en la salida del modelo sin validación determinista.
- No inventar valores que no aparezcan en el ticket.
- Usar null para datos ausentes o ilegibles.
- Conservar raw_description y valores extraídos.
- Marcar needs_review cuando exista ambigüedad.
- No registrar imágenes ni datos de pago en logs.
- No incorporar autenticación en este MVP.
- No crear microservicios.
- No añadir dependencias sin justificar su necesidad.
- Cada funcionalidad debe tener tests.
- Antes de cambiar una interfaz pública, actualizar el contrato y sus tests.

## Proceso obligatorio

1. Inspeccionar el repositorio.
2. Presentar el plan de archivos.
3. Implementar una unidad vertical.
4. Ejecutar lint y tests.
5. Corregir errores.
6. Resumir los cambios.
