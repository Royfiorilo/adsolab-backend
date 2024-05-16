FROM python:3.10-slim

COPY . /app
WORKDIR /app

RUN pip install pipenv
RUN pipenv install

RUN chmod +x startup.sh

ENTRYPOINT ["/bin/bash", "startup.sh"]
