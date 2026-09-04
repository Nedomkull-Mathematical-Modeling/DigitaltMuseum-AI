FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY dimu ./dimu

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin dimu \
    && pip install --no-cache-dir ".[api]"

USER dimu

EXPOSE 8000

CMD ["uvicorn", "dimu.api:app", "--host", "0.0.0.0", "--port", "8000"]
