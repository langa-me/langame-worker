
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

RUN apt-get update
RUN apt-get install -y --no-install-recommends git build-essential gcc python3-pip && pip3 install virtualenv

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir -e langame[all]
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app