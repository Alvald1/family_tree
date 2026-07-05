FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FAMILY_TREE_HOST=0.0.0.0 \
    FAMILY_TREE_PORT=8000 \
    FAMILY_TREE_DATA_DIR=/data/person_data \
    FAMILY_TREE_SOURCE_FILE=/data/source.txt

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY start_server.py ./
COPY tree_gen ./tree_gen
COPY site ./site

RUN mkdir -p /data/person_data \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"FAMILY_TREE_PORT\", \"8000\")}/api/health', timeout=3).read()"

CMD ["python", "start_server.py"]
