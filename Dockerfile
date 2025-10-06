FROM python:3.9-alpine3.13
LABEL maintainer="Antonio Santos"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
COPY ./scripts /scripts
WORKDIR /app
EXPOSE 8000


# Create virtualenv
ARG DEV=false
RUN python3 -m venv /py

# Upgrade pip
RUN /py/bin/pip install --upgrade pip
RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev linux-headers
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
        django-user && \
        mkdir -p /vol/web/media && \
        mkdir -p /vol/web/static && \
        chown -R django-user:django-user /vol && \
        chmod -R 755 /vol && \
        chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

USER django-user

CMD ["run.sh"]