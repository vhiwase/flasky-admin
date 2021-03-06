#!/bin/sh
source venv/bin/activate
while true; do
    flask dropdeploy
    flask deploy
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Deploying First Time command failed, retrying in 5 secs...
    sleep 5
done
exec gunicorn -b :5000 --access-logfile - --error-logfile - manage:app
