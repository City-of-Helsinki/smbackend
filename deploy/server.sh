#!/bin/bash

echo "NOTICE: Get static files for serving"
./manage.py collectstatic --no-input

echo "NOTICE: Start the uwsgi web server"
exec uwsgi --http :8000 --wsgi-file deploy/wsgi.py --static-map /static=/srv/smbackend/static
