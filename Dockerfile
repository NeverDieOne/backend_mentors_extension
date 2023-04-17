FROM python:3.11.0-alpine

EXPOSE 8000

WORKDIR /code

RUN pip install --upgrade pip
RUN apk add gcc musl-dev libffi-dev
RUN pip install poetry

COPY . /code

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "main.py"]