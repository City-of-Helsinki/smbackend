#!/bin/bash

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"
ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

LOG_FILE="/tmp/smbackend-import-$(date "+%Y-%m-%d-%H-%M").log"

if [ -f $ROOT_PATH/local_update_config ]; then
    $ROOT_PATH/local_update_config
fi
    
echo --------------------------------- >> $LOG_FILE
echo "$(date "$TIMESTAMP_FORMAT") Starting import" >> $LOG_FILE
echo --------------------------------- >> $LOG_FILE
    
cd $ROOT_PATH

python manage.py services_import --traceback --organizations --departments --services --units >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi

python manage.py update_index -a 1 >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi

curl -X PURGE http://10.1.2.123/servicemap >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    cat $LOG_FILE
    exit 1
fi
