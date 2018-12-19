FROM python:3.6

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git gdal-bin

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "-u", "./manage.py", "runserver", "0.0.0.0:8000"]
