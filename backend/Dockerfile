FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# app.main imports retrieval at module load (query router) and cascade/
# graph/rfi lazily per-request (schedule/topological dispatch, graph
# traversal, RFI matching) -- all four must be present for the image to
# boot and for those endpoints to work. sld/ingestion/benchmark are
# dev-time/offline-batch tools never imported by the live API, so they're
# deliberately left out of the runtime image.
COPY app ./app
COPY cascade ./cascade
COPY graph ./graph
COPY retrieval ./retrieval
COPY rfi ./rfi

RUN pip install --no-cache-dir .

COPY tests ./tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
