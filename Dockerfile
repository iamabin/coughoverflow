FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN ARCH="$(dpkg --print-architecture)" && \
    wget https://github.com/CSSE6400/CoughOverflow-Engine/releases/download/v1.0/overflowengine-${ARCH} -O overflowengine && \
    chmod +x overflowengine


COPY pyproject.toml poetry.lock README.md ./
COPY api ./api
COPY run.py ./



RUN pip install --upgrade pip && pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install

EXPOSE 8080
CMD ["python", "run.py"]