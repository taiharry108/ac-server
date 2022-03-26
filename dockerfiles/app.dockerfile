FROM python:3.9-alpine

# set working directory
WORKDIR /code
RUN mkdir /static

# set environment varibles
# prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apk --update add gcc make g++ zlib-dev libffi-dev

# install python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# add app
# COPY ./webapp /code/webapp
COPY ./logging.conf /code/logging.conf
COPY ./config.yml /code/config.yml
COPY ./alembic.ini /code/alembic.ini
COPY ./alembic /code/