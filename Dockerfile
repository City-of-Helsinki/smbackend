# ==============================
FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase
# ==============================

# Branch or tag used to pull python-uwsgi-common.
ARG UWSGI_COMMON_REF=main

ENV TZ="Europe/Helsinki"
ENV PYTHONDONTWRITEBYTECODE=True
ENV PYTHONUNBUFFERED=True
# Default for URL prefix, handled by uwsgi, ignored by devserver
# Works like this: "/example" -> http://hostname.domain.name/example
ENV DJANGO_URL_PREFIX=/

WORKDIR /app
USER root

COPY --from=ghcr.io/astral-sh/uv:0.11.24@sha256:99ea34acedc870ba4ad11a1f540a1c04267c9f30aadc465a94406f52dfda2c36 /uv /uvx /usr/local/bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/app-root \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./

RUN dnf update -y && dnf install -y \
    nmap-ncat \
    gettext \
    postgresql \
    && uv sync --frozen --no-dev --inexact --group prod \
    && uwsgi --build-plugin https://github.com/City-of-Helsinki/uwsgi-sentry \
    && dnf clean all

# Build and copy specific python-uwsgi-common files.
ADD https://github.com/City-of-Helsinki/python-uwsgi-common/archive/${UWSGI_COMMON_REF}.tar.gz /usr/src/
RUN mkdir -p /usr/src/python-uwsgi-common && \
    tar --strip-components=1 -xzf /usr/src/${UWSGI_COMMON_REF}.tar.gz -C /usr/src/python-uwsgi-common && \
    cp /usr/src/python-uwsgi-common/uwsgi-base.ini /app/ && \
    uwsgi --build-plugin /usr/src/python-uwsgi-common && \
    rm -rf /usr/src/${UWSGI_COMMON_REF}.tar.gz && \
    rm -rf /usr/src/python-uwsgi-common

# Munigeo will fetch data to this directory
RUN mkdir -p /app/data && chgrp -R 0 /app/data && chmod -R g+w /app/data

ENTRYPOINT ["./docker-entrypoint.sh"]
EXPOSE 8000/tcp

# ==============================
FROM appbase AS development
# ==============================

ENV DEV_SERVER=True
RUN uv sync --frozen --inexact
COPY . .
USER default

# ==============================
FROM appbase AS staticbuilder
# ==============================

ENV STATIC_ROOT=/app/static
COPY . .
RUN python manage.py collectstatic --noinput

# ==============================
FROM appbase AS production
# ==============================

COPY --from=staticbuilder /app/static /app/static
COPY . .

RUN python manage.py compilemessages

USER default
