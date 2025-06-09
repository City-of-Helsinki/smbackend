# Using Ubuntu base for access to GDAL PPA
FROM ubuntu:22.04
WORKDIR /smbackend

# tzdata installation requires settings frontend
RUN apt-get update && \
    TZ="Europe/Helsinki" DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip gdal-bin uwsgi uwsgi-plugin-python3 libgdal-dev postgresql-client netcat gettext git-core libpq-dev voikko-fi libvoikko-dev dialog openssh-server \
    && ln -s /usr/bin/pip3 /usr/local/bin/pip \
    && ln -s /usr/bin/python3 /usr/local/bin/python \
    && apt-get clean
  
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Enable SSH
RUN echo "root:Docker!" | chpasswd
COPY sshd_config /etc/ssh/

COPY . .
COPY data data_from_github
RUN chmod u+x ./docker-entrypoint.sh
RUN chmod u+x ./manage.py

EXPOSE 8000 2222

# Munigeo will fetch data to this directory
RUN mkdir -p /smbackend/data && chgrp -R 0 /smbackend/data && chmod -R g+w /smbackend/data

ENTRYPOINT ["./docker-entrypoint.sh"]