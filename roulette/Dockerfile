ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

# NOWY: Instalacja zależności systemowych PRZED instalacją pakietów Pythona
# Dodano --no-install-recommends i rm -rf /var/lib/apt/lists/* dla mniejszego rozmiaru obrazu
RUN apt-get update && \
    apt-get install -y libpq-dev gcc --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

COPY . /code

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "roulette_project.asgi:application"]