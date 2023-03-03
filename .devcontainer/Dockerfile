FROM python:3.11-slim

RUN apt-get update && apt-get -y install \
    git \
    curl

# Poetry
ENV POETRY_VERSION=1.4.0
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

RUN echo 'PATH="${PATH}:${POETRY_VENV}/bin"' >> /root/.bashrc && \
    echo '. ${POETRY_VENV}/bin/activate' >> /root/.bashrc
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# CODE
WORKDIR /code
COPY poetry.lock pyproject.toml ./
RUN poetry check && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction
