# Using Ubuntu base for access to GDAL PPA
FROM public.ecr.aws/ubuntu/ubuntu:22.04 AS appbase
WORKDIR /smbackend

# tzdata installation requires settings frontend
RUN apt-get update && \
    TZ="Europe/Helsinki" DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip gdal-bin uwsgi uwsgi-plugin-python3 postgresql-client netcat gettext git-core libpq-dev voikko-fi libvoikko-dev && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip && \
    ln -s /usr/bin/python3 /usr/local/bin/python \
    && apt-get clean

COPY requirements.txt .

RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# smbackend needs only static files, media is not used
ENV STATIC_ROOT /srv/smbackend/static
RUN mkdir -p /srv/smbackend/static

ENV SECRET_KEY "only-for-build"
RUN python manage.py compilemessages
RUN python manage.py collectstatic

# Munigeo will fetch data to this directory
RUN mkdir -p /smbackend/data && chgrp -R 0 /smbackend/data && chmod -R g+w /smbackend/data


ENTRYPOINT ["./docker-entrypoint.sh"]

# ==============================
FROM appbase AS development
# ==============================

COPY requirements-dev.txt .
RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -r requirements-dev.txt

# ==============================
FROM appbase as production
# ==============================
# Openshift starts the container process with group zero and random ID
# we mimic that here with nobody and group zero
USER nobody:0
