FROM python:3.10-slim

COPY . /app
WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2
RUN pip install pipenv
RUN pipenv install

RUN chmod +x startup.sh

ENTRYPOINT ["/bin/bash", "startup.sh"]
