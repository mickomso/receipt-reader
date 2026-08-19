# Decisiones del MVP

## Frontend

SvelteKit + TypeScript.

## Backend

FastAPI + Python 3.12.

## Modelo

Gemini multimodal a través de LangChain.

## Salida

Modelos Pydantic y salida estructurada.

## Orquestación

LangGraph con un grafo explícito, no un agente autónomo libre.

## Persistencia

SQLite para el MVP local.

## Ficheros

Directorio local `data/uploads`.

## Ejecución

Procesamiento síncrono en la primera versión, con interfaz de estado preparada
para evolucionar a jobs asíncronos.

## Moneda

EUR.

## Idioma

Tickets españoles inicialmente.

## Privacidad

No almacenar logs con imagen, número de tarjeta ni texto completo.
