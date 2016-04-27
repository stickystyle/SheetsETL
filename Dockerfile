FROM python:2.7-alpine
MAINTAINER Ryan Parrish <ryan@stickystyle.net>


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt
RUN touch /credentials.txt

CMD [ "python", "./src/loader.py" , "--noauth_local_webserver"]
