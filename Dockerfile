FROM python:3.10

WORKDIR /app

ENV PYTHONPATH="/app:${PYTHONPATH}"

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./ 

RUN poetry install --no-interaction

COPY . .

RUN poetry install --no-interaction

CMD ["poetry", "run", "python", "main.py"]
