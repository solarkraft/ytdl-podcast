FROM python:3.10

WORKDIR /app

RUN pip3 install poetry

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml

RUN poetry install --no-root --no-interaction --no-ansi -vvv

COPY . .

CMD poetry run waitress-serve --host 0.0.0.0 --port 8080 'server:app'
EXPOSE 8080
