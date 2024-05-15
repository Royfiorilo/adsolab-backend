FROM python:3.10-slim

ENV HOME=/

# Set working directory in the container
WORKDIR $HOME

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock ./

# Install pipenv and project dependencies
RUN pip install pipenv && \
    PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --ignore-pipfile


RUN chmod +x startup

# Run the app
CMD ["/bin/bash", "startup"]