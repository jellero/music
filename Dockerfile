FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MUSIC_STUDIO_DATA=/app/data

WORKDIR /app

COPY pyproject.toml README.md ./
COPY music_studio ./music_studio
RUN pip install --upgrade pip && pip install .

RUN useradd --create-home --uid 10001 studio && mkdir -p /app/data && chown -R studio:studio /app
USER studio

EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

CMD ["music-studio", "start", "--host", "0.0.0.0", "--port", "8000"]
