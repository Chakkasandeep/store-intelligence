# Hugging Face Docker Space — API + dashboard on port 7860
# https://huggingface.co/docs/hub/spaces-sdks-docker

FROM node:20-alpine AS dashboard
WORKDIR /fe
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY dashboard ./
ENV VITE_API_URL=
ENV VITE_STORE_ID=ST1008
RUN npm run build

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY backend ./backend
COPY pipeline ./pipeline
COPY scripts ./scripts
COPY configs ./configs
COPY data ./data
COPY tests ./tests
COPY docs ./docs
COPY DESIGN.md CHOICES.md pytest.ini ./

COPY --from=dashboard /fe/dist ./dashboard/dist

COPY docker/entrypoint_hf.sh ./docker/entrypoint_hf.sh
RUN sed -i 's/\r$//' docker/entrypoint_hf.sh && chmod +x docker/entrypoint_hf.sh

ENV PYTHONPATH=/app
ENV EVENTS_JSONL=/app/data/events/output.jsonl
ENV PORT=7860

EXPOSE 7860
CMD ["/bin/sh", "/app/docker/entrypoint_hf.sh"]
