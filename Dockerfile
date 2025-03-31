FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock README.md ./
COPY api ./api
COPY run.py ./
COPY instance ./instance


RUN pip install --upgrade pip && pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install

EXPOSE 8080
CMD ["python", "run.py"]