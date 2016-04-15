FROM python:3.5-alpine
MAINTAINER Ryan Parrish <ryan@stickystyle.net>


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app
