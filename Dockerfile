FROM python:3.10-slim

ENV HOME=/app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

WORKDIR $HOME

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv
RUN pipenv install

COPY startup.sh  ./
COPY app/ ./
RUN chmod +x startup.sh

ENTRYPOINT ["/bin/bash", "startup.sh"]
