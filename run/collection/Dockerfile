
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim
# TODO: alpine / scratch

COPY .pypirc /root/.pypirc
COPY pip.conf /root/.config/pip/pip.conf
COPY requirements.txt requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential gcc && \
    pip install --no-cache-dir -r requirements.txt

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN rm -rf /root/.cache/pip && rm -rf /root/.config/pip
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 4 --threads 8 --timeout 0 main:app