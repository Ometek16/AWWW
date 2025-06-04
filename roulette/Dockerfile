ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

ENV SECRET_KEY "ExZByaHdR4EpYIy5TnQSfhGT9epdJKrrur9RKDqf3ulSZiHy0d"
RUN python manage.py collectstatic --noinput
RUN apt-get update && apt-get install -y libpq-dev gcc

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "roulette_project.asgi:application"]

