FROM python:3.6
WORKDIR /servicemap

RUN apt-get update && apt-get install -y gdal-bin postgresql-client netcat

COPY requirements.txt .
COPY deploy/requirements.txt ./deploy/requirements.txt

RUN pip install --no-cache-dir -r deploy/requirements.txt

COPY . .

RUN mkdir -p www/media

ENV APPLY_MIGRATIONS true
ENTRYPOINT ["./docker-entrypoint.sh"]
