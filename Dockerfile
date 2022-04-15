FROM python:3.10-alpine

ENV FLASK_APP manage.py
ENV FLASK_CONFIG docker

RUN adduser -D vaibhav
USER vaibhav

WORKDIR /usr/src/app

COPY requirements requirements
RUN python -m venv venv
RUN venv/bin/pip install -r requirements/docker.txt

COPY app app
COPY migrations migrations
COPY manage.py config.py boot.sh ./

# runtime configuration
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]