FROM python:3.9-alpine3.13
LABEL maintainer="Antonio Santos"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000


# Create virtualenv
ARG DEV=false
RUN python3 -m venv /py

# Upgrade pip
RUN /py/bin/pip install --upgrade pip
RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev
# Install dependencies
RUN /py/bin/pip install -r /tmp/requirements.txt  && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi
RUN rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

USER django-user