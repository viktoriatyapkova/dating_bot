FROM python:3.10

WORKDIR /app

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-interaction --no-root

COPY . .

RUN poetry install --only main --no-interaction

CMD ["poetry", "run", "python", "main.py"]