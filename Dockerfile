# ==============================
FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase
# ==============================

ENV TZ="Europe/Helsinki"
ENV PYTHONDONTWRITEBYTECODE=True
ENV PYTHONUNBUFFERED=True
# Default for URL prefix, handled by uwsgi, ignored by devserver
# Works like this: "/example" -> http://hostname.domain.name/example
ENV DJANGO_URL_PREFIX=/

WORKDIR /app
USER root

COPY requirements.txt .

RUN dnf update -y && dnf install -y \
    nmap-ncat \
    gettext \
    postgresql \
    && pip install -U pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && uwsgi --build-plugin https://github.com/City-of-Helsinki/uwsgi-sentry \
    && dnf clean all

# Munigeo will fetch data to this directory
RUN mkdir -p /app/data && chgrp -R 0 /app/data && chmod -R g+w /app/data

ENTRYPOINT ["./docker-entrypoint.sh"]
EXPOSE 8000/tcp

# ==============================
FROM appbase AS development
# ==============================

ENV DEV_SERVER=True

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

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
