FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*


RUN pip install poetry

RUN mkdir -p /root/.aws

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --no-interaction

COPY api ./api
COPY run.py ./

EXPOSE 8080
CMD ["poetry", "run", "python", "run.py"]