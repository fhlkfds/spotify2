FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Keep image builds fast and deterministic by installing deps before source copy.
COPY pyproject.toml README.md ./
COPY app ./app
COPY analytics ./analytics
COPY db ./db
COPY spotify ./spotify
COPY exports ./exports

RUN pip install --no-cache-dir --no-compile --no-build-isolation . \
    && find /usr/local -type d -name "__pycache__" -prune -exec rm -rf {} +

EXPOSE 8501

CMD ["sh", "-c", "python -m db.init_db && streamlit run app/main.py --server.address=0.0.0.0 --server.port=8501"]
