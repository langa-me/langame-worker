FROM nvidia/cuda:11.5.0-base-ubuntu20.04
USER root
RUN apt-get update
RUN apt-get install -y --no-install-recommends python3.8 python3-pip build-essential gcc && pip3 install virtualenv

RUN virtualenv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

ARG USER=docker
ARG UID=1000
ARG GID=1000
# default password for user
ARG PW=docker
# Option1: Using unencrypted password/ specifying password
RUN useradd -m ${USER} --uid=${UID} && echo "${USER}:${PW}" | chpasswd
RUN mkdir -p /home/${USER}
RUN chown ${USER} /home/${USER}
# Setup default user, when enter docker container
WORKDIR /home/${USER}

COPY socialis ./socialis/
COPY ./setup.py ./setup.py
RUN pip install -e .

# FROM python:3.8-slim AS build-image
# COPY --from=compile-image /opt/venv /opt/venv

# Make sure we use the virtualenv:
# ENV PATH="/opt/venv/bin:$PATH"
# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED 0

# Copy local code to the container image.
# ENV APP_HOME /app
# WORKDIR $APP_HOME
# COPY --from=compile-image /socialis.egg-info socialis.egg-info
USER ${UID}:${GID}

ENTRYPOINT ["/opt/venv/bin/python", "./socialis/main.py"]
CMD ["--svc_path", "./svc.json"]
