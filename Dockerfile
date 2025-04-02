FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    pipx \
    wget \
    curl \
    build-essential \
    steghide \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry

WORKDIR /app

RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        wget https://github.com/CSSE6400/CoughOverflow-Engine/releases/download/v1.0/overflowengine-amd64 -O overflowengine; \
    else \
        wget https://github.com/CSSE6400/CoughOverflow-Engine/releases/download/v1.0/overflowengine-arm64 -O overflowengine; \
    fi && \
    chmod +x overflowengine

COPY pyproject.toml poetry.lock README.md ./
COPY api ./api
COPY run.py ./

RUN pipx run poetry install --no-root

EXPOSE 8080

CMD ["pipx", "run", "poetry", "run", "python", "run.py"]
