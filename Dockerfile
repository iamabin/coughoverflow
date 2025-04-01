FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    build-essential \
    wget \
    curl \
    pipx \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry

WORKDIR /app

RUN ARCH="$(dpkg --print-architecture)" && \
    wget https://github.com/CSSE6400/CoughOverflow-Engine/releases/download/v1.0/overflowengine-${ARCH} -O overflowengine && \
    chmod +x overflowengine

COPY pyproject.toml poetry.lock README.md ./
COPY api ./api
COPY run.py ./

ENV POETRY_VIRTUALENVS_CREATE=true
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN pipx run poetry install --no-root

EXPOSE 8080
CMD ["/app/.venv/bin/python", "run.py"]